import { describe, expect, it } from 'vitest'

import { TODOS_ROUTE } from '@/app/routes'

import { SIDEBAR_NAV } from './index'

describe('sidebar nav', () => {
  it('includes todos entry wired to /todos', () => {
    expect(SIDEBAR_NAV).toContainEqual(
      expect.objectContaining({
        id: 'todos',
        label: 'Todos',
        route: TODOS_ROUTE
      })
    )
  })
})

