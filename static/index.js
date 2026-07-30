window.PageAdminusers = {
  template: '#page-adminwallets',
  delimiters: ['${', '}'],

  data: function () {
    return {
      // ── Upload state ──
      csvTab: 'create',
      uploadState: {
        file: null,
        loading: false
      },
      deleteUploadState: {
        file: null,
        loading: false
      },

      // ── Source wallet selector ──
      adminWallets: [],
      selectedSourceWallet: null,

      // ── Batch result returned from the API ──
      batchResult: null,
      deleteBatchResult: null,

      // ── Result modal state ──
      resultDialogOpen: false,
      resultDownloaded: false,
      deleteResultDialogOpen: false,
      deleteResultDownloaded: false,

      // ── Error table columns ──
      errorColumns: [
        {name: 'wallet_name', label: 'Wallet Name', field: 'wallet_name', align: 'left'},
        {name: 'error', label: 'Error', field: 'error', align: 'left'}
      ],
      deleteErrorColumns: [
        {name: 'wallet_id', label: 'Wallet ID', field: 'wallet_id', align: 'left'},
        {name: 'error', label: 'Error', field: 'error', align: 'left'}
      ],

      // ── Wallet registry (history) table ──
      walletsList: [],
      walletsTable: {
        search: '',
        loading: false,
        columns: [
          {
            name: 'wallet_name',
            label: 'Wallet Name',
            field: 'wallet_name',
            align: 'left',
            sortable: true
          },
          {
            name: 'id',
            label: 'Wallet ID',
            field: 'id',
            align: 'left',
            sortable: false
          },
          {
            name: 'include_admin_key',
            label: 'Key Type',
            field: 'include_admin_key',
            align: 'left',
            sortable: false
          },
          {
            name: 'created_at',
            label: 'Created',
            field: 'created_at',
            align: 'left',
            sortable: true
          }
        ],
        pagination: {
          sortBy: 'created_at',
          rowsPerPage: 10,
          page: 1,
          descending: true,
          rowsNumber: 10
        }
      }
    }
  },

  computed: {
    errorRows() {
      if (!this.batchResult) return []
      return this.batchResult.rows.filter(r => r.status === 'error')
    },
    deleteErrorRows() {
      if (!this.deleteBatchResult) return []
      return this.deleteBatchResult.rows.filter(r => r.status === 'error')
    }
  },

  watch: {
    'walletsTable.search': {
      handler() {
        this.getManagedWallets()
      }
    }
  },

  methods: {

    // ──────────────────────────────────────────────
    //  CSV Upload & Processing
    // ──────────────────────────────────────────────

    async uploadCSV() {
      if (!this.uploadState.file) return

      this.uploadState.loading = true
      this.batchResult = null

      try {
        const formData = new FormData()
        formData.append('file', this.uploadState.file)
        if (this.selectedSourceWallet) {
          formData.append('source_wallet_id', this.selectedSourceWallet.id)
        }

        const response = await fetch('/adminwallets/api/v1/wallets/upload', {
          method: 'POST',
          headers: {
            'X-API-KEY': this.g.user.wallets[0].adminkey
          },
          body: formData
        })

        if (!response.ok) {
          const err = await response.json()
          throw new Error(err.detail || 'Upload failed.')
        }

        this.batchResult = await response.json()
        this.resultDownloaded = false
        this.resultDialogOpen = true
        await this.getManagedWallets()

        if (this.batchResult.success_count > 0) {
          this.$q.notify({
            type: 'positive',
            message: `${this.batchResult.success_count} wallet(s) created successfully.`
          })
        }
        if (this.batchResult.error_count > 0) {
          this.$q.notify({
            type: 'warning',
            message: `${this.batchResult.error_count} wallet(s) failed. See the error table.`
          })
        }

      } catch (error) {
        this.$q.notify({
          type: 'negative',
          message: error.message || 'An error occurred while processing the CSV.'
        })
      } finally {
        this.uploadState.loading = false
        this.uploadState.file = null
      }
    },

    // ──────────────────────────────────────────────
    //  CSV Download (generated client-side)
    // ──────────────────────────────────────────────

    downloadResultCSV() {
      if (!this.batchResult) return

      const headers = ['wallet_name', 'wallet_id', 'admin_key', 'invoice_key', 'initial_balance', 'status', 'error']
      const rows = this.batchResult.rows.map(r => [
        r.wallet_name || '',
        r.wallet_id || '',
        r.admin_key || '',
        r.invoice_key || '',
        r.initial_balance != null ? r.initial_balance : '',
        r.status || '',
        r.error || ''
      ])

      const csvContent = [headers, ...rows]
        .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
        .join('\n')

      const blob = new Blob([csvContent], {type: 'text/csv;charset=utf-8;'})
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'wallets_' + new Date().toISOString().slice(0, 19).replace(/:/g, '-') + '.csv'
      link.click()
      URL.revokeObjectURL(url)

      // Mark as downloaded — changes button state in the modal
      this.resultDownloaded = true
    },

    closeResultDialog() {
      this.resultDialogOpen = false
      // Clear batchResult only after closing so data persists while modal is open
      this.batchResult = null
      this.resultDownloaded = false
    },

    downloadTemplate() {
      const content = 'wallet_name,include_admin_key,initial_balance\nAlice,1,100\nBob,0,50\nCharlie,1,0\n'
      const blob = new Blob([content], {type: 'text/csv;charset=utf-8;'})
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'wallets_template.csv'
      link.click()
      URL.revokeObjectURL(url)
    },

    async uploadDeleteCSV() {
      if (!this.deleteUploadState.file) return

      this.deleteUploadState.loading = true
      this.deleteBatchResult = null

      try {
        const formData = new FormData()
        formData.append('file', this.deleteUploadState.file)

        const response = await fetch('/adminwallets/api/v1/wallets/delete-csv', {
          method: 'POST',
          headers: {
            'X-API-KEY': this.g.user.wallets[0].adminkey
          },
          body: formData
        })

        if (!response.ok) {
          const err = await response.json()
          throw new Error(err.detail || 'Upload failed.')
        }

        this.deleteBatchResult = await response.json()
        this.deleteResultDownloaded = false
        this.deleteResultDialogOpen = true
        await this.getManagedWallets()

        if (this.deleteBatchResult.success_count > 0) {
          this.$q.notify({
            type: 'positive',
            message: `${this.deleteBatchResult.success_count} wallet(s) deleted successfully.`
          })
        }
        if (this.deleteBatchResult.error_count > 0) {
          this.$q.notify({
            type: 'warning',
            message: `${this.deleteBatchResult.error_count} wallet(s) failed. See the error table.`
          })
        }

      } catch (error) {
        this.$q.notify({
          type: 'negative',
          message: error.message || 'An error occurred while processing the CSV.'
        })
      } finally {
        this.deleteUploadState.loading = false
        this.deleteUploadState.file = null
      }
    },

    downloadDeleteResultCSV() {
      if (!this.deleteBatchResult) return

      const headers = ['wallet_id', 'funds_swept', 'status', 'error']
      const rows = this.deleteBatchResult.rows.map(r => [
        r.wallet_id || '',
        r.funds_swept != null ? r.funds_swept : '',
        r.status || '',
        r.error || ''
      ])

      const csvContent = [headers, ...rows]
        .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
        .join('\n')

      const blob = new Blob([csvContent], {type: 'text/csv;charset=utf-8;'})
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'deleted_wallets_' + new Date().toISOString().slice(0, 19).replace(/:/g, '-') + '.csv'
      link.click()
      URL.revokeObjectURL(url)

      this.deleteResultDownloaded = true
    },

    closeDeleteResultDialog() {
      this.deleteResultDialogOpen = false
      this.deleteBatchResult = null
      this.deleteResultDownloaded = false
    },

    downloadDeleteTemplate() {
      const content = 'wallet_id\n<wallet_id_1>\n<wallet_id_2>\n'
      const blob = new Blob([content], {type: 'text/csv;charset=utf-8;'})
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'delete_wallets_template.csv'
      link.click()
      URL.revokeObjectURL(url)
    },

    // ──────────────────────────────────────────────
    //  Wallet Registry (History)
    // ──────────────────────────────────────────────

    async getManagedWallets(props) {
      try {
        this.walletsTable.loading = true
        const params = LNbits.utils.prepareFilterQuery(this.walletsTable, props)
        const {data} = await LNbits.api.request(
          'GET',
          `/adminwallets/api/v1/wallets/paginated?${params}`,
          null
        )
        this.walletsList = data.data
        this.walletsTable.pagination.rowsNumber = data.total
      } catch (error) {
        LNbits.utils.notifyApiError(error)
      } finally {
        this.walletsTable.loading = false
      }
    },

    async deleteManagedWallet(walletId) {
      await LNbits.utils
        .confirmDialog(
          'Remove this wallet from the registry?\n\n' +
          'Note: this does NOT delete the actual wallet from LNbits.'
        )
        .onOk(async () => {
          try {
            await LNbits.api.request(
              'DELETE',
              '/adminwallets/api/v1/wallets/' + walletId,
              null
            )
            await this.getManagedWallets()
            this.$q.notify({type: 'positive', message: 'Wallet removed from registry.'})
          } catch (error) {
            LNbits.utils.notifyApiError(error)
          }
        })
    },

    // ──────────────────────────────────────────────
    //  Utilities
    // ──────────────────────────────────────────────

    dateFromNow(date) {
      return moment(date).fromNow()
    },

    async loadAdminWallets() {
      try {
        const {data} = await LNbits.api.request(
          'GET',
          '/adminwallets/api/v1/admin-wallets',
          null
        )
        this.adminWallets = data
        if (data.length === 1) {
          this.selectedSourceWallet = data[0]
        }
      } catch (error) {
        LNbits.utils.notifyApiError(error)
      }
    }
  },

  async created() {
    await Promise.all([this.getManagedWallets(), this.loadAdminWallets()])
  }
}