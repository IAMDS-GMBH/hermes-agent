import type * as React from 'react'
import { useEffect, useMemo, useState } from 'react'

import { PageLoader } from '@/components/page-loader'
import { Badge } from '@/components/ui/badge'
import { Codicon } from '@/components/ui/codicon'
import { TextTab, TextTabMeta } from '@/components/ui/text-tab'
import { useI18n } from '@/i18n'
import { cn } from '@/lib/utils'
import { notifyError } from '@/store/notifications'
import { useGatewayRequest } from '../gateway/hooks/use-gateway-request'

import { useRefreshHotkey } from '../hooks/use-refresh-hotkey'
import { useRouteEnumParam } from '../hooks/use-route-enum-param'
import { PAGE_INSET_X } from '../layout-constants'
import { PageSearchShell } from '../page-search-shell'
import { includesQuery, prettyName } from '../settings/helpers'

const HUB_MODES = ['agents', 'skills'] as const
type HubMode = (typeof HUB_MODES)[number]

interface LiteLLMAgent {
  id: string
  name: string
  description?: string
}

interface LiteLLMSkill {
  id: string
  name: string
  description?: string
  source?: string
}

function filteredAgents(agents: LiteLLMAgent[], query: string): LiteLLMAgent[] {
  const q = query.trim().toLowerCase()

  return agents
    .filter(agent => {
      if (!q) {
        return true
      }

      return (
        includesQuery(agent.name, q) ||
        includesQuery(agent.description || '', q)
      )
    })
    .sort((a, b) => (a.name || '').localeCompare(b.name || ''))
}

function filteredSkills(skills: LiteLLMSkill[], query: string): LiteLLMSkill[] {
  const q = query.trim().toLowerCase()

  return skills
    .filter(skill => {
      if (!q) {
        return true
      }

      return (
        includesQuery(skill.name, q) ||
        includesQuery(skill.description || '', q)
      )
    })
    .sort((a, b) => (a.name || '').localeCompare(b.name || ''))
}

interface HubViewProps extends React.ComponentProps<'section'> {}

export function HubView({ ...props }: HubViewProps) {
  const { t } = useI18n()
  const { requestGateway } = useGatewayRequest()
  const [mode, setMode] = useRouteEnumParam('tab', HUB_MODES, 'agents')

  const [query, setQuery] = useState('')
  const [agents, setAgents] = useState<LiteLLMAgent[] | null>(null)
  const [skills, setSkills] = useState<LiteLLMSkill[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [resolvedUrl, setResolvedUrl] = useState<string | null>(null)
  const [installing, setInstalling] = useState<{ id: string; skill: LiteLLMSkill } | null>(null)
  const [installProgress, setInstallProgress] = useState<string>('')

  // Refresh handlers
  const refresh = async () => {
    setError(null)
    setResolvedUrl(null)

    try {
      if (mode === 'agents') {
        const data = await requestGateway<{ agents: unknown[]; resolved_url?: string }>('litellm_hub.agents', { limit: 100 })
        console.log('[Hub] agents resolved_url:', data?.resolved_url)
        setResolvedUrl(data?.resolved_url || null)
        const agentsList = (data?.agents || []).map((agent: unknown) => {
          const a = agent as Record<string, unknown>
          return {
            id: String(a.id || a.name || ''),
            name: String(a.name || ''),
            description: a.description ? String(a.description) : undefined
          }
        })
        setAgents(agentsList)
      } else {
        const data = await requestGateway<{ skills: unknown[]; resolved_url?: string }>('litellm_hub.skills', { limit: 100 })
        console.log('[Hub] skills resolved_url:', data?.resolved_url)
        setResolvedUrl(data?.resolved_url || null)
        const skillsList = (data?.skills || []).map((skill: unknown) => {
          const s = skill as Record<string, unknown>
          let sourceStr = undefined
          if (s.source) {
            const srcObj = s.source as Record<string, unknown>
            if (srcObj.source === 'github' && srcObj.repo) {
              sourceStr = `github:${srcObj.repo}`
            }
          }
          return {
            id: String(s.id || s.name || ''),
            name: String(s.name || ''),
            description: s.description ? String(s.description) : undefined,
            source: sourceStr
          }
        })
        setSkills(skillsList)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      console.error('[Hub] load error:', message)
      setError(message)
      notifyError(err, `Failed to load ${mode}`)
    }
  }

  const handleInstallSkill = async (skill: LiteLLMSkill) => {
    setInstalling({ id: skill.id, skill })
    setInstallProgress('Starting installation...')

    try {
      setInstallProgress('Downloading skill from GitHub...')
      const result = await requestGateway<{ success: boolean; message: string }>('litellm_hub.skill_install', {
        skill_id: skill.id,
        skill_name: skill.name,
        source: skill.source
      })

      if (result?.success) {
        setInstallProgress(`✓ Successfully installed: ${skill.name}`)
        setTimeout(() => setInstalling(null), 2000)
      } else {
        setInstallProgress(`✗ Installation failed: ${result?.message || 'Unknown error'}`)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      setInstallProgress(`✗ Error: ${message}`)
      notifyError(err, `Failed to install ${skill.name}`)
    }
  }

  // Initial load
  useEffect(() => {
    void refresh()
  }, [mode])

  // Refresh hotkey (Cmd+R / Ctrl+R)
  useRefreshHotkey(refresh)

  // Compute filtered lists
  const filteredAgentsList = useMemo(() => {
    return agents ? filteredAgents(agents, query) : null
  }, [agents, query])

  const filteredSkillsList = useMemo(() => {
    return skills ? filteredSkills(skills, query) : null
  }, [skills, query])

  const isLoading = (mode === 'agents' && agents === null) || (mode === 'skills' && skills === null)

  return (
    <section {...props} className={cn('flex flex-col overflow-hidden', props.className)}>
      <PageSearchShell
        searchValue={query}
        onSearchChange={setQuery}
        searchPlaceholder={
          mode === 'agents' ? 'Search agents...' : 'Search skills...'
        }
        tabs={
          <>
            <TextTab
              active={mode === 'agents'}
              onClick={() => setMode('agents')}
              className="data-[active]:bg-accent/5"
            >
              <span>Agents</span>
              {filteredAgentsList && (
                <Badge variant="outline" className="ml-2 pointer-events-none">
                  {filteredAgentsList.length}
                </Badge>
              )}
            </TextTab>

            <TextTab
              active={mode === 'skills'}
              onClick={() => setMode('skills')}
              className="data-[active]:bg-accent/5"
            >
              <span>Skills</span>
              {filteredSkillsList && (
                <Badge variant="outline" className="ml-2 pointer-events-none">
                  {filteredSkillsList.length}
                </Badge>
              )}
            </TextTab>
          </>
        }
      >
        {resolvedUrl && (
          <div className="px-4 py-2 text-xs text-muted-foreground bg-secondary/50 border-b border-border m-0 font-mono break-all">
            Fetching from: {resolvedUrl}
          </div>
        )}

        {error && (
          <div className="px-4 py-3 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 m-4 rounded">
            {error}
          </div>
        )}

        {isLoading ? (
          <PageLoader />
        ) : mode === 'agents' ? (
          <AgentsList agents={filteredAgentsList || []} query={query} />
        ) : (
          <SkillsList skills={filteredSkillsList || []} query={query} onInstall={handleInstallSkill} />
        )}
        
        {installing && <SkillInstallModal skill={installing.skill} progress={installProgress} />}
      </PageSearchShell>
    </section>
  )
}

interface AgentsListProps {
  agents: LiteLLMAgent[]
  query: string
}

function AgentsList({ agents, query }: AgentsListProps) {
  return (
    <div className="overflow-y-auto flex-1">
      {agents.length === 0 ? (
        <div className={cn('flex items-center justify-center h-full text-sm text-muted-foreground', PAGE_INSET_X)}>
          {query ? 'No agents match your search.' : 'No agents available.'}
        </div>
      ) : (
        <div className={cn('space-y-1 p-4', PAGE_INSET_X)}>
          {agents.map(agent => (
            <div
              key={agent.id}
              className="p-3 rounded border border-border bg-card hover:bg-accent/5 transition-colors"
            >
              <div className="flex items-start gap-2">
                <Codicon className="mt-1" name="robot" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-foreground">{agent.name}</div>
                  {agent.description && (
                    <div className="text-sm text-muted-foreground mt-1 line-clamp-2">
                      {agent.description}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

interface SkillsListProps {
  skills: LiteLLMSkill[]
  query: string
  onInstall?: (skill: LiteLLMSkill) => void
}

function SkillsList({ skills, query, onInstall }: SkillsListProps) {
  return (
    <div className="overflow-y-auto flex-1">
      {skills.length === 0 ? (
        <div className={cn('flex items-center justify-center h-full text-sm text-muted-foreground', PAGE_INSET_X)}>
          {query ? 'No skills match your search.' : 'No skills available.'}
        </div>
      ) : (
        <div className={cn('space-y-1 p-4', PAGE_INSET_X)}>
          {skills.map(skill => (
            <div
              key={skill.id}
              className="p-3 rounded border border-border bg-card hover:bg-accent/5 transition-colors"
            >
              <div className="flex items-start gap-2">
                <Codicon className="mt-1" name="lightbulb" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-foreground">{skill.name}</div>
                  {skill.description && (
                    <div className="text-sm text-muted-foreground mt-1 line-clamp-2">
                      {skill.description}
                    </div>
                  )}
                  {skill.source && (
                    <div className="text-xs text-muted-foreground mt-2">
                      Source: {skill.source}
                    </div>
                  )}
                </div>
                {onInstall && (
                  <button
                    onClick={() => onInstall(skill)}
                    className="ml-2 px-2.5 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors flex-shrink-0"
                  >
                    Install
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

interface SkillInstallModalProps {
  skill: LiteLLMSkill
  progress: string
}

function SkillInstallModal({ skill, progress }: SkillInstallModalProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background border border-border rounded-lg shadow-lg w-full max-w-md mx-4 p-6">
        <h2 className="text-lg font-semibold mb-4">Installing {skill.name}</h2>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 rounded-full bg-blue-500 animate-pulse"></div>
            <p className="text-sm">{progress}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
