# AdminWallets — LNbits Extension

## ¿Qué hace y para qué sirve?

**AdminWallets** es una extensión para administradores de LNbits que permite gestionar billeteras de forma centralizada y masiva. Está diseñada para casos de uso institucionales o plataformas que necesitan incorporar a muchos usuarios a la vez, reduciendo el trabajo manual al mínimo.

El acceso a todas las funciones está restringido exclusivamente a cuentas con rol de **administrador**.

---

## Funcionalidades

### 1. Creación Masiva de Wallets por CSV

Sube un archivo `.csv` con la lista de billeteras a crear. La extensión las procesa en lote, devuelve un reporte de resultados y permite descargar las credenciales.

**Formato del CSV de entrada:**

| Columna | Requerida | Valores | Descripción |
|---|---|---|---|
| `wallet_name` | ✅ | Texto | Nombre de la billetera a crear |
| `include_admin_key` | ✅ | `1` / `0` | `1` = incluir admin key + invoice key; `0` = solo invoice key |
| `initial_balance` | ❌ | Entero ≥ 0 | Sats a cargar en la billetera al momento de crearla. Dejar en blanco o `0` para no fondear. |

**Ejemplo de CSV:**
```csv
wallet_name,include_admin_key,initial_balance
Alice,1,100
Bob,0,50
Charlie,1,
Dave,0,0
```

#### Fondeo Inicial (`initial_balance`)
- Antes de crear cualquier billetera, el sistema **verifica que la wallet origen del administrador tenga fondos suficientes** para cubrir el total de sats solicitados (incluyendo reservas de fees de LNbits). Si no alcanza, el proceso se aborta completamente sin crear ninguna billetera.
- El administrador puede elegir desde cuál de sus wallets se descontarán los fondos a través del selector en la interfaz.
- Si el admin tiene una sola wallet, se preselecciona automáticamente.
- Los fondos se transfieren como una transacción interna de LNbits (sin comisiones de red).

**CSV de resultados descargable:**

| Columna | Descripción |
|---|---|
| `wallet_name` | Nombre de la billetera |
| `wallet_id` | ID generado por LNbits |
| `admin_key` | Clave de administrador (vacía si `include_admin_key=0`) |
| `invoice_key` | Clave de solo lectura / invoice |
| `initial_balance` | Sats efectivamente fondeados (`0` si ninguno) |
| `status` | `success` o `error` |
| `error` | Descripción del error si aplica |

---

### 2. Borrado Masivo de Wallets por CSV

Sube un archivo `.csv` con los IDs de las billeteras que deseas eliminar. Por cada una, el sistema:

1. **Verifica que no pertenezca al propio administrador** (protección de seguridad).
2. **Transfiere los fondos al administrador** si la billetera tiene saldo (sweep automático).
3. **Elimina la billetera del núcleo de LNbits** (borrado real, no solo del registro).

**Formato del CSV de entrada:**

| Columna | Requerida | Descripción |
|---|---|---|
| `wallet_id` | ✅ | ID de la billetera a eliminar |

**Endpoint:** `POST /api/v1/wallets/delete-csv`

---

### 3. Listado Paginado y Filtrable

Visualiza todas las billeteras creadas por la extensión en una tabla con:
- Búsqueda por nombre o ID.
- Ordenamiento por nombre o fecha de creación.
- Paginación configurable.

---

### 4. Borrado Individual de Wallets

Elimina billeteras una por una desde la tabla de registro. Se aplica la misma lógica de seguridad del borrado masivo:
- Transferencia automática de fondos si la billetera tiene saldo.
- Verificación de que no sea la propia wallet del administrador.
- Borrado real en el núcleo de LNbits.

---

## API Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/admin-wallets` | Lista las billeteras del administrador (para selector de funding) |
| `POST` | `/api/v1/wallets/upload` | Crea billeteras en lote desde CSV |
| `POST` | `/api/v1/wallets/delete-csv` | Borra billeteras en lote desde CSV |
| `GET` | `/api/v1/wallets/paginated` | Lista paginada de billeteras gestionadas |
| `GET` | `/api/v1/wallets/{wallet_id}` | Detalle de una billetera gestionada |
| `DELETE` | `/api/v1/wallets/{wallet_id}` | Borra una billetera individual |
| `GET` | `/api/v1/settings` | Obtiene la configuración de la extensión |
| `PUT` | `/api/v1/settings` | Actualiza la configuración de la extensión |

---

## Seguridad

- Todos los endpoints requieren autenticación de **administrador** (`X-API-KEY` con admin key).
- La extensión **nunca borra wallets del administrador** — cualquier intento de incluir las propias wallets del admin en una operación de borrado se rechaza con un error explícito.
- Las credenciales de las billeteras creadas **solo están disponibles en el CSV descargable** y no se almacenan en la extensión.
