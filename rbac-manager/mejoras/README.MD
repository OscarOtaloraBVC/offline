# Arquitectura de Sincronización RBAC

```text
+-----------------------------------+             +-----------------------------------+
|    Cluster 1 (Primary)            |             |   Cluster 2 (Secondary)           |
|                                   |             |                                   |
|  [Certificados] <--(Eventos)-->   |             |  [Certificados] <--(Eventos)-->   |
|        |                          |             |        |                          |
|  [RBAC Manager App] <-> [SQLite]  |             |  [RBAC Manager App] <-> [SQLite]  |
+-----------|-----------------------+             +----------------|------------------+
            |                                                      |
            |               +------------------------+             |
            +-------------- | Capa de Sincronización | ------------+
                            |      Litestream        |
                            +------------------------+
```