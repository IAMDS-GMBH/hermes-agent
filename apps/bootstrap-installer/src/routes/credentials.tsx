import { useState } from 'react'
import { Button } from '../components/button'
import { startInstall } from '../store'
import { AlertCircle } from 'lucide-react'

export interface CredentialsData {
  apiKey: string
  baseUrl: string
  modelName: string
  memoryApiUrl?: string
  emailAddress?: string
  emailPassword?: string
  imapServer?: string
  smtpServer?: string
}

export default function Credentials() {
  const [formData, setFormData] = useState<CredentialsData>({
    apiKey: '',
    baseUrl: 'https://api.openai.com/v1',
    modelName: 'gpt-4o',
    memoryApiUrl: '',
    emailAddress: '',
    emailPassword: '',
    imapServer: '',
    smtpServer: ''
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [showEmailSection, setShowEmailSection] = useState(false)

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.apiKey.trim()) {
      newErrors.apiKey = 'API Key is required'
    }
    if (!formData.baseUrl.trim()) {
      newErrors.baseUrl = 'Base URL is required'
    }
    if (!formData.modelName.trim()) {
      newErrors.modelName = 'Model name is required'
    }

    // Email validation: only apply when the optional section is enabled.
    if (showEmailSection) {
      if (!formData.emailAddress?.trim()) {
        newErrors.emailAddress = 'Email address required for gateway setup'
      }
      if (!formData.emailPassword?.trim()) {
        newErrors.emailPassword = 'Password required for gateway setup'
      }
      if (!formData.imapServer?.trim()) {
        newErrors.imapServer = 'IMAP server required for gateway setup'
      }
      if (!formData.smtpServer?.trim()) {
        newErrors.smtpServer = 'SMTP server required for gateway setup'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    // Clean up optional empty fields
    const cleaned: CredentialsData = {
      apiKey: formData.apiKey.trim(),
      baseUrl: formData.baseUrl.trim(),
      modelName: formData.modelName.trim(),
      memoryApiUrl: formData.memoryApiUrl?.trim() || undefined,
      emailAddress: showEmailSection ? formData.emailAddress?.trim() || undefined : undefined,
      emailPassword: showEmailSection ? formData.emailPassword?.trim() || undefined : undefined,
      imapServer: showEmailSection ? formData.imapServer?.trim() || undefined : undefined,
      smtpServer: showEmailSection ? formData.smtpServer?.trim() || undefined : undefined
    }

    await startInstall({ credentials: cleaned })
  }

  const handleChange = (field: keyof CredentialsData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev }
        delete next[field]
        return next
      })
    }
  }

  return (
    <div className="hermes-fade-in flex h-full flex-col overflow-auto bg-background px-8 py-10">
      <div className="mx-auto w-full max-w-xl">
        <h1 className="mb-2 text-2xl font-semibold text-foreground">
          Configuration
        </h1>
        <p className="mb-8 text-sm text-muted-foreground">
          Enter your KI provider credentials and optional settings.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* KI Provider Section */}
          <fieldset className="rounded-lg border border-border bg-muted/20 p-4">
            <legend className="mb-4 block text-sm font-medium text-foreground">
              KI Provider
            </legend>

            <div className="space-y-4">
              {/* API Key */}
              <div>
                <label htmlFor="apiKey" className="block text-sm font-medium text-foreground">
                  API Key <span className="text-red-500">*</span>
                </label>
                <input
                  id="apiKey"
                  type="password"
                  value={formData.apiKey}
                  onChange={(e) => handleChange('apiKey', e.target.value)}
                  placeholder="sk-..."
                  className="mt-1 w-full rounded border border-input bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
                {errors.apiKey && (
                  <p className="mt-1 flex items-center gap-1 text-xs text-red-500">
                    <AlertCircle className="h-3 w-3" />
                    {errors.apiKey}
                  </p>
                )}
              </div>

              {/* Base URL */}
              <div>
                <label htmlFor="baseUrl" className="block text-sm font-medium text-foreground">
                  Base URL <span className="text-red-500">*</span>
                </label>
                <input
                  id="baseUrl"
                  type="text"
                  value={formData.baseUrl}
                  onChange={(e) => handleChange('baseUrl', e.target.value)}
                  placeholder="https://api.openai.com/v1"
                  className="mt-1 w-full rounded border border-input bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
                {errors.baseUrl && (
                  <p className="mt-1 flex items-center gap-1 text-xs text-red-500">
                    <AlertCircle className="h-3 w-3" />
                    {errors.baseUrl}
                  </p>
                )}
              </div>

              {/* Model Name */}
              <div>
                <label htmlFor="modelName" className="block text-sm font-medium text-foreground">
                  Model Name <span className="text-red-500">*</span>
                </label>
                <input
                  id="modelName"
                  type="text"
                  value={formData.modelName}
                  onChange={(e) => handleChange('modelName', e.target.value)}
                  placeholder="gpt-4o"
                  className="mt-1 w-full rounded border border-input bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
                {errors.modelName && (
                  <p className="mt-1 flex items-center gap-1 text-xs text-red-500">
                    <AlertCircle className="h-3 w-3" />
                    {errors.modelName}
                  </p>
                )}
              </div>
            </div>
          </fieldset>

          {/* Memory API (Optional) */}
          <fieldset className="rounded-lg border border-border bg-muted/20 p-4">
            <legend className="mb-4 block text-sm font-medium text-foreground">
              Centralized Memory API <span className="text-xs text-muted-foreground">(optional)</span>
            </legend>

            <div>
              <label htmlFor="memoryApiUrl" className="block text-sm font-medium text-foreground">
                Memory API URL
              </label>
              <input
                id="memoryApiUrl"
                type="text"
                value={formData.memoryApiUrl || ''}
                onChange={(e) => handleChange('memoryApiUrl', e.target.value)}
                placeholder="https://api.memory.example.com"
                className="mt-1 w-full rounded border border-input bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Leave blank to skip. Will use your API key for authentication.
              </p>
            </div>
          </fieldset>

          {/* Email Gateway (Optional) */}
          <fieldset className="rounded-lg border border-border bg-muted/20 p-4">
            <legend className="mb-4 flex items-center gap-2">
              <input
                type="checkbox"
                id="enableEmail"
                checked={showEmailSection}
                onChange={(e) => {
                  const enabled = e.target.checked
                  setShowEmailSection(enabled)
                  if (!enabled) {
                    setErrors((prev) => {
                      const next = { ...prev }
                      delete next.emailAddress
                      delete next.emailPassword
                      delete next.imapServer
                      delete next.smtpServer
                      return next
                    })
                  }
                }}
                className="h-4 w-4 rounded border-input"
              />
              <label htmlFor="enableEmail" className="text-sm font-medium text-foreground cursor-pointer">
                Email Gateway <span className="text-xs text-muted-foreground">(optional)</span>
              </label>
            </legend>

            {showEmailSection && (
              <div className="space-y-4">
                {/* Email Address */}
                <div>
                  <label htmlFor="emailAddress" className="block text-sm font-medium text-foreground">
                    Email Address <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="emailAddress"
                    type="email"
                    value={formData.emailAddress || ''}
                    onChange={(e) => handleChange('emailAddress', e.target.value)}
                    placeholder="agent@example.com"
                    className="mt-1 w-full rounded border border-input bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  {errors.emailAddress && (
                    <p className="mt-1 flex items-center gap-1 text-xs text-red-500">
                      <AlertCircle className="h-3 w-3" />
                      {errors.emailAddress}
                    </p>
                  )}
                </div>

                {/* Email Password */}
                <div>
                  <label htmlFor="emailPassword" className="block text-sm font-medium text-foreground">
                    Password / App Password <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="emailPassword"
                    type="password"
                    value={formData.emailPassword || ''}
                    onChange={(e) => handleChange('emailPassword', e.target.value)}
                    placeholder="••••••••"
                    className="mt-1 w-full rounded border border-input bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  {errors.emailPassword && (
                    <p className="mt-1 flex items-center gap-1 text-xs text-red-500">
                      <AlertCircle className="h-3 w-3" />
                      {errors.emailPassword}
                    </p>
                  )}
                </div>

                {/* IMAP Server */}
                <div>
                  <label htmlFor="imapServer" className="block text-sm font-medium text-foreground">
                    IMAP Server <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="imapServer"
                    type="text"
                    value={formData.imapServer || ''}
                    onChange={(e) => handleChange('imapServer', e.target.value)}
                    placeholder="imap.gmail.com"
                    className="mt-1 w-full rounded border border-input bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  {errors.imapServer && (
                    <p className="mt-1 flex items-center gap-1 text-xs text-red-500">
                      <AlertCircle className="h-3 w-3" />
                      {errors.imapServer}
                    </p>
                  )}
                </div>

                {/* SMTP Server */}
                <div>
                  <label htmlFor="smtpServer" className="block text-sm font-medium text-foreground">
                    SMTP Server <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="smtpServer"
                    type="text"
                    value={formData.smtpServer || ''}
                    onChange={(e) => handleChange('smtpServer', e.target.value)}
                    placeholder="smtp.gmail.com"
                    className="mt-1 w-full rounded border border-input bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  {errors.smtpServer && (
                    <p className="mt-1 flex items-center gap-1 text-xs text-red-500">
                      <AlertCircle className="h-3 w-3" />
                      {errors.smtpServer}
                    </p>
                  )}
                </div>
              </div>
            )}
          </fieldset>

          {/* Form Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="submit"
              size="lg"
              className="min-w-32"
            >
              Install Hermes
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
