import { defineStore } from 'pinia'
import {
  cancelBranchTicket,
  getActiveBranchTicket,
  getBranches,
  issueBranchTicket,
} from '@/api/backend'
import { useAuthStore } from './auth'

export const useBranchTicketStore = defineStore('branchTicket', {
  state: () => ({
    branches: [],
    selectedBranchId: null,
    ticket: null,
    loading: false,
  }),

  getters: {
    selectedBranch: (state) => state.branches.find((branch) => branch.id === state.selectedBranchId) || null,
  },

  actions: {
    async load() {
      const auth = useAuthStore()
      this.loading = true
      try {
        const [branches, ticket] = await Promise.all([
          getBranches(),
          getActiveBranchTicket(auth.userId),
        ])
        this.branches = branches
        this.ticket = ticket
        if (ticket) this.selectedBranchId = ticket.branch_id
      } finally {
        this.loading = false
      }
    },

    select(branchId) {
      if (!this.ticket) this.selectedBranchId = branchId
    },

    async issue({ purpose = '일반 상담', summary_id = null } = {}) {
      if (!this.selectedBranchId) return null
      const auth = useAuthStore()
      this.loading = true
      try {
        this.ticket = await issueBranchTicket(this.selectedBranchId, {
          user_id: auth.userId,
          summary_id,
          purpose,
        })
        return this.ticket
      } finally {
        this.loading = false
      }
    },

    async cancel() {
      if (!this.ticket) return
      this.loading = true
      try {
        await cancelBranchTicket(this.ticket.id)
        this.ticket = null
        await this.load()
      } finally {
        this.loading = false
      }
    },
  },
})
