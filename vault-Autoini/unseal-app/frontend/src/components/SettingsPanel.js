import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  Card,
  CardContent,
  Slider,
  Alert,
  CircularProgress,
  Divider,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Save as SaveIcon,
  Settings as SettingsIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import toast from 'react-hot-toast';

const SettingsPanel = () => {
  const [settings, setSettings] = useState({
    threshold: 2,
    namespace: 'vault',
    container_name: 'vault',
    monitor_interval: 30,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [password, setPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await api.get('/settings');
      setSettings(response.data);
    } catch (error) {
      toast.error('Error cargando configuraciones');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    if (settings.threshold < 1 || settings.threshold > 10) {
      toast.error('El threshold debe estar entre 1 y 10');
      return;
    }

    if (settings.monitor_interval < 10 || settings.monitor_interval > 300) {
      toast.error('El intervalo debe estar entre 10 y 300 segundos');
      return;
    }

    setSaving(true);
    try {
      await api.put('/settings', {
        threshold: settings.threshold,
        namespace: settings.namespace,
        container_name: settings.container_name,
        monitor_interval: settings.monitor_interval,
        password: password || undefined,
      });
      toast.success('Configuraciones guardadas correctamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error guardando configuraciones');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      toast.error('Las contraseñas no coinciden');
      return;
    }

    if (newPassword.length < 4) {
      toast.error('La contraseña debe tener al menos 4 caracteres');
      return;
    }

    setChangingPassword(true);
    try {
      await api.post('/auth/update-password', {
        current_password: password,
        new_password: newPassword,
      });
      toast.success('Contraseña actualizada correctamente');
      setPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error actualizando contraseña');
    } finally {
      setChangingPassword(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Grid container spacing={3}>
        {/* Configuraciones Generales */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, background: 'rgba(26, 26, 26, 0.8)' }}>
            <Box display="flex" alignItems="center" gap={1} mb={3}>
              <SettingsIcon sx={{ color: '#00bcd4' }} />
              <Typography variant="h6">Configuraciones Generales</Typography>
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography gutterBottom>Threshold (llaves requeridas)</Typography>
                <Slider
                  value={settings.threshold}
                  onChange={(_, value) => setSettings({ ...settings, threshold: value })}
                  min={1}
                  max={10}
                  marks={[
                    { value: 1, label: '1' },
                    { value: 5, label: '5' },
                    { value: 10, label: '10' },
                  ]}
                  valueLabelDisplay="auto"
                />
                <Typography variant="body2" color="textSecondary">
                  Número de llaves necesarias para desbloquear Vault
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  label="Namespace de Kubernetes"
                  fullWidth
                  value={settings.namespace}
                  onChange={(e) => setSettings({ ...settings, namespace: e.target.value })}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  label="Nombre del contenedor de Vault"
                  fullWidth
                  value={settings.container_name}
                  onChange={(e) => setSettings({ ...settings, container_name: e.target.value })}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  label="Intervalo de monitoreo (segundos)"
                  type="number"
                  fullWidth
                  value={settings.monitor_interval}
                  onChange={(e) => setSettings({ 
                    ...settings, 
                    monitor_interval: parseInt(e.target.value) || 30 
                  })}
                  helperText="Mínimo 10 segundos, máximo 300 segundos"
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  label="Contraseña del Admin (para cambios críticos)"
                  type="password"
                  fullWidth
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  helperText="Requerida para guardar cambios en threshold"
                />
              </Grid>

              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={autoRefresh}
                      onChange={(e) => setAutoRefresh(e.target.checked)}
                    />
                  }
                  label="Auto-refrescar dashboard"
                />
              </Grid>

              <Grid item xs={12}>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSaveSettings}
                  disabled={saving}
                  fullWidth
                  sx={{
                    background: 'linear-gradient(45deg, #00bcd4 30%, #00acc1 90%)',
                    '&:hover': {
                      background: 'linear-gradient(45deg, #00acc1 30%, #00838f 90%)',
                    },
                  }}
                >
                  {saving ? <CircularProgress size={24} /> : 'Guardar Configuraciones'}
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Seguridad */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, background: 'rgba(26, 26, 26, 0.8)' }}>
            <Box display="flex" alignItems="center" gap={1} mb={3}>
              <SecurityIcon sx={{ color: '#ff4081' }} />
              <Typography variant="h6">Seguridad</Typography>
            </Box>

            <Card sx={{ mb: 3, background: 'rgba(255, 64, 129, 0.05)' }}>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>
                  Cambiar Contraseña del Admin
                </Typography>
                <Alert severity="warning" sx={{ mb: 2 }}>
                  Esta acción cambiará la contraseña de acceso a la interfaz web
                </Alert>

                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      label="Contraseña Actual"
                      type="password"
                      fullWidth
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      label="Nueva Contraseña"
                      type="password"
                      fullWidth
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      label="Confirmar Nueva Contraseña"
                      type="password"
                      fullWidth
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      error={newPassword !== confirmPassword && confirmPassword.length > 0}
                      helperText={
                        newPassword !== confirmPassword && confirmPassword.length > 0
                          ? 'Las contraseñas no coinciden'
                          : ''
                      }
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Button
                      variant="contained"
                      color="secondary"
                      onClick={handleChangePassword}
                      disabled={changingPassword || !password || !newPassword || newPassword !== confirmPassword}
                      fullWidth
                    >
                      {changingPassword ? <CircularProgress size={24} /> : 'Cambiar Contraseña'}
                    </Button>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            <Alert severity="info">
              <Typography variant="body2">
                <strong>Nota de Seguridad:</strong> Las llaves de unseal se almacenan cifradas
                con AES-256-GCM. La contraseña del admin se utiliza para derivar la llave maestra
                usando PBKDF2 con 600,000 iteraciones.
              </Typography>
            </Alert>
          </Paper>
        </Grid>

        {/* Información del Sistema */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, background: 'rgba(26, 26, 26, 0.8)' }}>
            <Typography variant="h6" gutterBottom>
              Información del Sistema
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Versión
                    </Typography>
                    <Typography variant="h6">1.0.0</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Threshold Actual
                    </Typography>
                    <Typography variant="h6">{settings.threshold}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Namespace
                    </Typography>
                    <Typography variant="h6">{settings.namespace}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Intervalo
                    </Typography>
                    <Typography variant="h6">{settings.monitor_interval}s</Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SettingsPanel;