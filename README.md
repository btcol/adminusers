# AdminWallets - Extensión para LNbits

## ¿Qué hace y para qué sirve?

La extensión **AdminWallets** permite a los administradores de una instancia de LNbits gestionar billeteras (wallets) de forma centralizada y eficiente. Su objetivo principal es facilitar la creación, administración y eliminación de "Managed Wallets" (billeteras gestionadas por el administrador).

Es especialmente útil para casos de uso institucionales o plataformas que necesitan incorporar a una gran cantidad de usuarios al mismo tiempo, ya que cuenta con capacidades de procesamiento por lotes (batch processing).

### Funcionalidades principales:
- **Gestión de Wallets:** Permite listar, crear y borrar billeteras individuales.
- **Creación por Lotes (Batch Processing):** Soporta la subida de un archivo CSV para crear múltiples billeteras automáticamente en una sola operación.
- **Configuración de Extensión:** Permite establecer configuraciones avanzadas, por ejemplo, limitar el uso de la extensión de forma exclusiva para los administradores.
- **Vistas y Reportes:** Proporciona un listado paginado y filtrable de todas las wallets bajo la administración de la extensión.

## ¿Cómo se usa?

1. **Instalación y Activación:** Al instalar la extensión en tu servidor LNbits, los administradores tendrán acceso a un nuevo panel de control.
2. **Creación de Wallets Individuales:** Desde la interfaz de usuario (Frontend), puedes añadir manualmente nuevas wallets completando los detalles requeridos.
3. **Carga masiva vía CSV:** 
   - Prepara un archivo CSV siguiendo el formato requerido por la extensión.
   - Sube el archivo mediante la opción de "Upload CSV".
   - La extensión procesará el archivo en segundo plano, creará todas las billeteras y te permitirá descargar un reporte con los resultados (éxitos y errores).
4. **Administración y Borrado:** Puedes visualizar todas las wallets creadas desde la tabla principal y eliminar aquellas que ya no se necesiten.

*Esta extensión fue diseñada originalmente utilizando el LNbits Extension Builder y posteriormente ampliada para incluir capacidades de gestión masiva y configuraciones específicas de administrador.*
