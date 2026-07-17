import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Lock as LockIcon,
  LockOpen as UnlockIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import toast from 'react-hot-toast';

const MonitorDashboard = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [password, setPassword] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const { user, getToken } = useAuth();

  useEffect(() => {
    loadStatus();
    const interval = setInterval(() => {
      if (autoRefresh) {
        loadStatus();
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const loadStatus = async () => {
    try {
      setLoading(true);
      const response = await api.get('/monitor/status');
      setStatus(response.data);
    } catch (error) {
      toast.error('Error cargando estado del monitor');
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerUnseal = async () => {
    if (!password) {
      toast.error('Ingresa la contraseña del admin');
      return;
    }

    setTriggering(true);
    try {
      const response = await api.post('/monitor/trigger', {
        password: password,
      });
      
      toast.success(
        `Unseal completado: ${response.data.pods_unsealed}/${response.data.pods_processed} pods`
      );
      setDialogOpen(false);
      setPassword('');
      await loadStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error ejecutando unseal');
    } finally {
      setTriggering(false);
    }
  };

  const handleSetWorkerPassword = async () => {
    if (!password) {
      toast.error('Ingresa la contraseña del admin');
      return;
    }

    try {
      await api.post('/monitor/set-password', {
        password: password,
      });
      toast.success('Contraseña del worker configurada correctamente');
      setDialogOpen(false);
      setPassword('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error configurando contraseña');
    }
  };

  if (loading && !status) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const PodStatusCard = ({ pod }) => {
    const isSealed = pod.sealed;
    const isRunning = pod.running;
    
    return (
      <Card sx={{ mb: 2, background: 'rgba(26, 26, 26, 0.6)' }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography variant="h6" component="div">
                {pod.name}
              </Typography>
              <Box display="flex" gap={1} mt={1}>
                <Chip
                  size="small"
                  label={isRunning ? 'Running' : 'Stopped'}
                  color={isRunning ? 'success' : 'error'}
                />
                <Chip
                  size="small"
                  label={isSealed ? 'Sealed' : 'Unsealed'}
                  icon={isSealed ? <LockIcon /> : <UnlockIcon />}
                  color={isSealed ? 'warning' : 'success'}
                />
              </Box>
            </Box>
            <Box>
              {!isRunning && (
                <Tooltip title="El pod no está corriendo">
                  <ErrorIcon color="error" />
                </Tooltip>
              )}
              {isRunning && !isSealed && (
                <Tooltip title="Pod desbloqueado">
                  <CheckIcon color="success" />
                </Tooltip>
              )}
              {isRunning && isSealed && (
                <Tooltip title="Pod sellado - necesita unseal">
                  <LockIcon color="warning" />
                </Tooltip>
              )}
            </Box>
          </Box>
          {pod.error && (
            <Alert severity="warning" sx={{ mt: 1 }}>
              {pod.error}
            </Alert>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Box p={3}>
      <Grid container spacing={3}>
        {/* Resumen */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, background: 'rgba(26, 26, 26, 0.8)' }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h5" component="h1">
                Dashboard de Monitoreo
              </Typography>
              <Box>
                <Tooltip title="Refrescar estado">
                  <IconButton onClick={loadStatus} disabled={loading}>
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title={status?.running ? 'Worker activo' : 'Worker inactivo'}>
                  <Chip
                    label={status?.running ? 'Activo' : 'Inactivo'}
                    color={status?.running ? 'success' : 'error'}
                    size="small"
                  />
                </Tooltip>
              </Box>
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ background: 'rgba(0, 188, 212, 0.1)' }}>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Total Pods
                    </Typography>
                    <Typography variant="h4">
                      {status?.total_pods || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ background: 'rgba(255, 193, 7, 0.1)' }}>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Sellados
                    </Typography>
                    <Typography variant="h4" color="warning.main">
                      {status?.sealed_pods || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ background: 'rgba(76, 175, 80, 0.1)' }}>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Desbloqueados
                    </Typography>
                    <Typography variant="h4" color="success.main">
                      {status?.unsealed_pods || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ background: 'rgba(156, 39, 176, 0.1)' }}>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Worker
                    </Typography>
                    <Typography variant="h4">
                      {status?.running ? '🟢' : '🔴'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            <Box mt={3} display="flex" gap={2}>
              <Button
                variant="contained"
                startIcon={<PlayIcon />}
                onClick={() => setDialogOpen(true)}
                sx={{
                  background: 'linear-gradient(45deg, #00bcd4 30%, #00acc1 90%)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #00acc1 30%, #00838f 90%)',
                  },
                }}
              >
                Ejecutar Unseal Ahora
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={loadStatus}
                disabled={loading}
              >
                Refrescar
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Lista de Pods */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, background: 'rgba(26, 26, 26, 0.8)' }}>
            <Typography variant="h6" gutterBottom>
              Estado de Pods
            </Typography>
            {status?.pods_status?.length === 0 ? (
              <Alert severity="info">
                No se encontraron pods de Vault en el namespace configurado
              </Alert>
            ) : (
              <Box>
                {status?.pods_status?.map((pod, index) => (
                  <PodStatusCard key={index} pod={pod} />
                ))}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Diálogo de Unseal */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Ejecutar Unseal Manual</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              Se ejecutará un ciclo completo de desbloqueo en todos los pods de Vault.
            </Alert>
            <TextField
              label="Contraseña del Admin"
              type="password"
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              helperText="Necesaria para descifrar las llaves de unseal"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancelar</Button>
          <Button
            onClick={handleTriggerUnseal}
            variant="contained"
            disabled={triggering || !password}
            sx={{
              background: 'linear-gradient(45deg, #00bcd4 30%, #00acc1 90%)',
              '&:hover': {
                background: 'linear-gradient(45deg, #00acc1 30%, #00838f 90%)',
              },
            }}
          >
            {triggering ? <CircularProgress size={24} /> : 'Ejecutar Unseal'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MonitorDashboard;