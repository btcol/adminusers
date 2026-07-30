<template id="page-adminwallets">
  <div class="row q-col-gutter-md">

    <!-- ===================== LEFT COLUMN ===================== -->
    <div class="col-12 col-md-8 col-lg-7 q-gutter-y-md">

      <!-- ── Header card ── -->
      <q-card id="headerCard">
        <q-card-section>
          <div class="row items-center no-wrap">
            <div class="col">
              <span class="text-h5">Admin Wallet Manager</span>
              <div class="text-caption text-grey q-mt-xs">
                Upload a CSV to create wallets in bulk and download their credentials.
              </div>
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- ── CSV Upload card ── -->
      <q-card id="uploadCard">
        <q-card-section>
          <div class="row items-center q-mb-md">
            <q-icon name="upload_file" size="md" color="primary" />
            <div style="font-size: 20px; font-weight: 500; margin-left: 12px; letter-spacing: normal;">Upload CSV File</div>
          </div>

          <q-banner rounded class="q-mb-md bg-transparent" style="border: 1px solid var(--q-primary)">
            <template v-slot:avatar>
              <q-icon name="info" color="primary" />
            </template>
            <div class="text-body2">
              <strong>CSV format required:</strong> columns —
              <code>wallet_name</code>, <code>include_admin_key</code>,
              and optionally <code>initial_balance</code>
              (sats to fund the wallet on creation, defaults to 0).
            </div>
            <div class="q-mt-xs">
              <q-btn
                flat
                dense
                size="sm"
                color="primary"
                label="Download template"
                icon="file_download"
                @click="downloadTemplate"
              />
            </div>
          </q-banner>

          <!-- Source wallet selector -->
          <div class="q-mb-md">
            <q-select
              v-model="selectedSourceWallet"
              :options="adminWallets"
              option-value="id"
              option-label="name"
              label="Funding source wallet (required if using initial_balance)"
              filled
              dense
              clearable
              hint="Funds will be deducted from this wallet when creating wallets with initial balance."
            >
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>${ scope.opt.name }</q-item-label>
                    <q-item-label caption>${ scope.opt.balance_sat } sats</q-item-label>
                  </q-item-section>
                </q-item>
              </template>
              <template v-slot:selected-item="scope" v-if="selectedSourceWallet">
                <span>${ scope.opt.name } — <strong>${ scope.opt.balance_sat } sats</strong></span>
              </template>
            </q-select>
          </div>

          <div class="row q-col-gutter-md items-end">
            <div class="col">
              <q-file
                v-model="uploadState.file"
                label="Select CSV file"
                accept=".csv"
                filled
                dense
                clearable
                :disable="uploadState.loading"
              >
                <template v-slot:prepend>
                  <q-icon name="attach_file" />
                </template>
              </q-file>
            </div>
            <div class="col-auto">
              <q-btn
                id="processBtn"
                unelevated
                color="primary"
                icon="play_arrow"
                label="Process CSV"
                :disable="!uploadState.file || uploadState.loading"
                :loading="uploadState.loading"
                @click="uploadCSV"
              />
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- ── Result card (shown after processing) ── -->
      <q-card id="resultCard" v-if="batchResult">
        <q-card-section>
          <div class="row items-center q-mb-md">
            <div class="col text-h6">
              <q-icon name="summarize" class="q-mr-sm" />
              Processing Result
            </div>
            <div class="col-auto">
              <q-btn
                id="downloadResultBtn"
                unelevated
                color="positive"
                icon="file_download"
                label="Download CSV"
                @click="downloadResultCSV"
              />
            </div>
          </div>

          <!-- Summary chips -->
          <div class="row q-gutter-sm q-mb-md">
            <q-chip icon="check_circle" color="positive" text-color="white">
              ${ batchResult.success_count } created
            </q-chip>
            <q-chip
              v-if="batchResult.error_count > 0"
              icon="error"
              color="negative"
              text-color="white"
            >
              ${ batchResult.error_count } failed
            </q-chip>
            <q-chip icon="list" color="grey-7" text-color="white">
              ${ batchResult.total } total
            </q-chip>
            <q-chip
              v-if="batchResult.rows.some(r => r.initial_balance > 0)"
              icon="bolt"
              color="deep-orange"
              text-color="white"
            >
              ${ batchResult.rows.reduce((s, r) => s + (r.initial_balance || 0), 0) } sats funded
            </q-chip>
          </div>

          <!-- Error rows table -->
          <div v-if="batchResult.error_count > 0">
            <div class="text-subtitle2 q-mb-sm text-negative">
              <q-icon name="warning" class="q-mr-xs" />Failed rows
            </div>
            <q-table
              dense
              flat
              :rows="errorRows"
              :columns="errorColumns"
              row-key="wallet_name"
              hide-bottom
            />
          </div>

          <q-banner rounded class="q-mt-md bg-transparent" style="border: 1px solid orange">
            <template v-slot:avatar>
              <q-icon name="lock" color="orange" />
            </template>
            <span class="text-caption">
              Wallet credentials are included in the downloaded CSV only.
              They are not stored or shown here for security reasons.
            </span>
          </q-banner>
        </q-card-section>
      </q-card>

      <!-- ── Wallet History card ── -->
      <div class="q-mt-md">
        <span class="text-h6">Wallet Registry</span>
        <span class="text-caption text-grey q-ml-sm">
          (informational only — no keys are shown)
        </span>
      </div>

      <q-card id="historyCard">
        <q-card-section>
          <div class="row items-center no-wrap q-mb-md">
            <div class="col">
              <q-input
                :label="$t('search')"
                dense
                class="q-pr-xl"
                v-model="walletsTable.search"
              >
                <template v-slot:before>
                  <q-icon name="search" />
                </template>
                <template v-slot:append>
                  <q-icon
                    v-if="walletsTable.search !== ''"
                    name="close"
                    @click="walletsTable.search = ''"
                    class="cursor-pointer"
                  />
                </template>
              </q-input>
            </div>
            <div class="col-auto q-ml-sm">
              <q-btn
                flat
                color="grey"
                icon="refresh"
                @click="getManagedWallets()"
              >
                <q-tooltip>Refresh</q-tooltip>
              </q-btn>
            </div>
          </div>

          <q-table
            dense
            flat
            :rows="walletsList"
            row-key="id"
            :columns="walletsTable.columns"
            v-model:pagination="walletsTable.pagination"
            :loading="walletsTable.loading"
            @request="getManagedWallets"
          >
            <template v-slot:header="props">
              <q-tr :props="props">
                <q-th auto-width></q-th>
                <q-th v-for="col in props.cols" :key="col.name" :props="props">
                  ${ col.label }
                </q-th>
              </q-tr>
            </template>

            <template v-slot:body="props">
              <q-tr :props="props">
                <q-td auto-width>
                  <q-btn
                    flat
                    dense
                    size="xs"
                    icon="delete"
                    color="negative"
                    @click="deleteManagedWallet(props.row.id)"
                  >
                    <q-tooltip>Remove from registry</q-tooltip>
                  </q-btn>
                </q-td>

                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                  <div v-if="col.field === 'include_admin_key'">
                    <q-chip
                      dense
                      :color="col.value ? 'blue-2' : 'grey-3'"
                      :text-color="col.value ? 'blue-9' : 'grey-7'"
                      size="sm"
                    >
                      ${ col.value ? 'Admin + Invoice' : 'Invoice only' }
                    </q-chip>
                  </div>
                  <div v-else-if="col.field === 'created_at'">
                    <span v-text="dateFromNow(col.value)"></span>
                  </div>
                  <div v-else>${ col.value }</div>
                </q-td>
              </q-tr>
            </template>

            <template v-slot:no-data>
              <div class="full-width row flex-center text-grey q-gutter-sm q-py-lg">
                <q-icon name="inbox" size="2em" />
                <span>No wallets have been created yet.</span>
              </div>
            </template>
          </q-table>
        </q-card-section>
      </q-card>
    </div>

    <!-- ===================== RIGHT COLUMN ===================== -->
    <div class="col-12 col-md-4 col-lg-5 q-gutter-y-md">

      <!-- Info card -->
      <q-card>
        <q-card-section>
          <h6 class="text-subtitle1 q-my-none">adminwallets</h6>
          <p class="text-caption text-grey">creation and management of users and wallets</p>
        </q-card-section>
        <q-card-section class="q-pa-none">
          <q-separator />
          <q-list>
            <q-expansion-item group="extras" icon="info" label="How it works">
              <q-card>
                <q-card-section>
                  <ol class="text-body2 q-pl-md">
                    <li>Prepare a CSV with columns <code>wallet_name</code>, <code>include_admin_key</code> and optionally <code>initial_balance</code> (sats).</li>
                    <li>Select a source wallet if you want to fund the new wallets.</li>
                    <li>Upload the CSV using the form on the left.</li>
                    <li>Click <strong>Process CSV</strong> — wallets are created and funded instantly.</li>
                    <li>Download the result CSV with wallet credentials and funding status.</li>
                  </ol>
                  <q-banner rounded dense class="q-mt-sm bg-transparent" style="border: 1px solid orange">
                    <template v-slot:avatar>
                      <q-icon name="lock" color="orange" size="xs" />
                    </template>
                    <span class="text-caption">
                      Credentials are only available in the downloaded CSV.
                      Store it securely.
                    </span>
                  </q-banner>
                </q-card-section>
              </q-card>
            </q-expansion-item>

            <q-separator />

            <q-expansion-item group="extras" icon="table_chart" label="CSV format">
              <q-card>
                <q-card-section>
                  <div class="text-caption q-mb-sm">Input CSV example:</div>
                  <pre class="bg-grey-2 q-pa-sm rounded-borders text-caption">wallet_name,include_admin_key,initial_balance
Alice,1,100
Bob,0,50
Charlie,1,0</pre>
                  <div class="text-caption q-mt-md q-mb-sm">Output CSV includes:</div>
                  <ul class="text-caption q-pl-md">
                    <li><code>wallet_name</code></li>
                    <li><code>wallet_id</code></li>
                    <li><code>admin_key</code> (empty if include_admin_key=0)</li>
                    <li><code>invoice_key</code></li>
                    <li><code>initial_balance</code> (sats funded, 0 if none)</li>
                    <li><code>status</code></li>
                    <li><code>error</code></li>
                  </ul>
                </q-card-section>
              </q-card>
            </q-expansion-item>
          </q-list>
        </q-card-section>
      </q-card>

    </div>

  </div>
</template>