import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  IconButton,
  Chip,
  Stack,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  InputAdornment,
  Visibility,
  VisibilityOff,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  SwapVert as SwapIcon,
  VpnKey as KeyIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import toast from 'react-hot-toast';

const KeyManager = () => {
  const [keys, setKeys] = useState([]);
  const [threshold, setThreshold] = useState(2);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newKey, setNewKey] = useState('');
  const [password, setPassword] = useState('');
  const [viewPassword, setViewPassword] = useState('');
  const [showKeys, setShowKeys] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    loadKeys();
  }, []);

  const loadKeys = async (passwordParam = null) => {
    try {
      setLoading(true);
      let url = '/keys';
      if (passwordParam) {
        url += `?password=${encodeURIComponent(passwordParam)}`;
      }
      const response = await api.get(url);
      setKeys(response.data.keys || []);
      setThreshold(response.data.threshold || 2);
      if (passwordParam && response.data.keys.length > 0) {
        setShowKeys(true);
        toast.success(`Se cargaron ${response.data.keys.length} llaves`);
      } else if (passwordParam && response.data.keys.length === 0) {
        toast.error('No se encontraron llaves o la contraseña es incorrecta');
        setShowKeys(false);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error cargando llaves');
      setKeys([]);
      setShowKeys(false);
    } finally {
      setLoading(false);
    }
  };

  const handleAddKey = async () => {
    if (!newKey || newKey.length !== 44) {
      toast.error('La llave debe tener 44 caracteres');
      return;
    }

    if (!password) {
      toast.error('Debes ingresar la contraseña del admin');
      return;
    }

    try {
      await api.post('/keys', {
        key: newKey,
        password: password,
      });
      toast.success('Llave añadida correctamente');
      setDialogOpen(false);
      setNewKey('');
      setPassword('');
      // Recargar las llaves si ya están visibles
      if (showKeys) {
        await loadKeys(viewPassword);
      } else {
        await loadKeys();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error añadiendo llave');
    }
  };

  const handleDeleteKey = async (index) => {
    if (!window.confirm(`¿Estás seguro de eliminar la llave ${index + 1}?`)) {
      return;
    }

    const pwd = prompt('Ingresa la contraseña del admin para confirmar:');
    if (!pwd) return;

    try {
      await api.delete(`/keys/${index + 1}`, {
        data: { password: pwd },
      });
      toast.success('Llave eliminada correctamente');
      if (showKeys) {
        await loadKeys(viewPassword);
      } else {
        await loadKeys();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error eliminando llave');
    }
  };

  const handleReorder = async () => {
    if (keys.length < 2) {
      toast.error('Se necesitan al menos 2 llaves para reordenar');
      return;
    }

    const pwd = prompt('Ingresa la contraseña del admin para reordenar:');
    if (!pwd) return;

    try {
      const order = keys.map((_, i) => i + 1);
      // Intercambiar los dos últimos
      const last = order.length - 1;
      [order[last - 1], order[last]] = [order[last], order[last - 1]];
      
      await api.post('/keys/reorder', {
        order: order,
        password: pwd,
      });
      toast.success('Orden actualizado correctamente');
      if (showKeys) {
        await loadKeys(viewPassword);
      } else {
        await loadKeys();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error reordenando llaves');
    }
  };

  const handleViewKeys = () => {
    if (!viewPassword) {
      toast.error('Ingresa la contraseña del admin');
      return;
    }
    loadKeys(viewPassword);
  };

  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
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
      <Paper sx={{ p: 3, background: 'rgba(26, 26, 26, 0.8)' }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h5" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <KeyIcon sx={{ color: '#00bcd4' }} />
            Gestión de Llaves de Unseal
          </Typography>
          <Box>
            <Button
              variant="outlined"
              startIcon={<SwapIcon />}
              onClick={handleReorder}
              sx={{ mr: 1 }}
            >
              Reordenar
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setDialogOpen(true)}
              sx={{
                background: 'linear-gradient(45deg, #00bcd4 30%, #00acc1 90%)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #00acc1 30%, #00838f 90%)',
                },
              }}
            >
              Añadir Llave
            </Button>
          </Box>
        </Box>

        <Alert severity="info" sx={{ mb: 3 }}>
          Threshold actual: <strong>{threshold}</strong> - Se requieren {threshold} llaves para desbloquear Vault
        </Alert>

        {/* Campo para ver las llaves */}
        <Paper sx={{ p: 2, mb: 3, background: 'rgba(0, 188, 212, 0.05)' }}>
          <Typography variant="subtitle2" gutterBottom>
            Ver llaves almacenadas
          </Typography>
          <Box display="flex" gap={2} alignItems="center">
            <TextField
              label="Contraseña del Admin"
              type={showPassword ? 'text' : 'password'}
              value={viewPassword}
              onChange={(e) => setViewPassword(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleViewKeys();
                }
              }}
              sx={{ flex: 1 }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={handleTogglePasswordVisibility}>
                      {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              helperText="Ingresa la contraseña para ver las llaves almacenadas"
            />
            <Button
              variant="contained"
              onClick={handleViewKeys}
              sx={{
                background: 'linear-gradient(45deg, #00bcd4 30%, #00acc1 90%)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #00acc1 30%, #00838f 90%)',
                },
              }}
            >
              Ver Llaves
            </Button>
            {showKeys && (
              <Chip
                label={`${keys.length} llaves visibles`}
                color="success"
                size="small"
              />
            )}
          </Box>
        </Paper>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>#</TableCell>
                <TableCell>Llave</TableCell>
                <TableCell>Estado</TableCell>
                <TableCell align="right">Acciones</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {showKeys && keys.map((key, index) => (
                <TableRow key={index}>
                  <TableCell>{index + 1}</TableCell>
                  <TableCell>
                    <Chip
                      label={`${key.substring(0, 10)}...${key.substring(key.length - 10)}`}
                      sx={{ fontFamily: 'monospace', bgcolor: 'rgba(0, 188, 212, 0.1)' }}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={index < threshold ? 'Usada' : 'Backup'}
                      color={index < threshold ? 'primary' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      color="error"
                      onClick={() => handleDeleteKey(index)}
                      size="small"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {!showKeys && (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    <Typography color="textSecondary" sx={{ py: 3 }}>
                      🔒 Ingresa la contraseña del admin para ver las llaves almacenadas
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
              {showKeys && keys.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    <Typography color="textSecondary" sx={{ py: 3 }}>
                      No hay llaves configuradas. Añade al menos 2 llaves para el auto-unseal.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Diálogo para añadir llave */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Añadir Nueva Llave de Unseal</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Llave (44 caracteres base64)"
              fullWidth
              value={newKey}
              onChange={(e) => setNewKey(e.target.value)}
              placeholder="Ej: 8X3q... (44 caracteres)"
              helperText={newKey.length !== 44 ? `Longitud: ${newKey.length}/44` : '✓ Longitud correcta'}
              error={newKey.length > 0 && newKey.length !== 44}
            />
            <TextField
              label="Contraseña del Admin"
              type="password"
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              helperText="Se requiere para cifrar la llave"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancelar</Button>
          <Button
            onClick={handleAddKey}
            variant="contained"
            disabled={!newKey || !password}
            sx={{
              background: 'linear-gradient(45deg, #00bcd4 30%, #00acc1 90%)',
              '&:hover': {
                background: 'linear-gradient(45deg, #00acc1 30%, #00838f 90%)',
              },
            }}
          >
            Añadir
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default KeyManager;