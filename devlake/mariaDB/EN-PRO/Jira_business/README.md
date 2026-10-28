# Configuración de campos en la tabla issues

Para que configmap pueda adicionar datos en bddevlake se deben crear los campos a la tabla issues

```text
├── ⚙️ devlake-sync-configmap.yaml
├── ⚙️ devlake-sync-cronjob.yaml
├── ⚙️ devlake-sync-secret.yaml
```

## Adicion en tabla

```sql
ALTER TABLE issues ADD COLUMN event_report_date DATETIME NULL;
ALTER TABLE issues ADD COLUMN event_start_date  DATETIME NULL;
ALTER TABLE issues ADD COLUMN event_end_date    DATETIME NULL;
ALTER TABLE issues ADD COLUMN end_definitive_correction_mttr    DATETIME NULL;
```

## Eliminar en tabla

```sql
ALTER TABLE issues
  DROP COLUMN IF EXISTS event_report_date,
  DROP COLUMN IF EXISTS event_start_date,
  DROP COLUMN IF EXISTS event_end_date,
  DROP COLUMN IF EXISTS end_definitive_correction_mttr;
```

## Prueba Kubectl

### 1. Aplicar manifiestos

```bash
kubectl delete -f devlake-sync-secret.yaml
kubectl delete -f devlake-sync-configmap.yaml
kubectl delete -f devlake-sync-cronjob.yaml
```

### 2. Prueba manual inmediata (sin esperar a la 1 AM)

```bash
kubectl create job --from=cronjob/devlake-jira-sync test-sync-01 -n devlake
```

### 3. Ver logs en tiempo real

```bash
kubectl logs -f -l job-name=test-sync-01 -n devlake
```

### 4. Limpiar job de prueba

```bash
kubectl delete job test-sync-01 -n devlake
```