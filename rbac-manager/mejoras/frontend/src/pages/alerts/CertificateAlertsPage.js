// frontend/src/pages/alerts/CertificateAlertsPage.js
import React, { useState, useEffect } from 'react';
import { getUserAlerts, createAlert, deleteAlert, checkExpiringCertificates } from '../../services/alertService';
import { getAllUsers } from '../../services/userService';
import Swal from 'sweetalert2';

const CertificateAlertsPage = () => {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [daysBefore, setDaysBefore] = useState(7);
  const [alerts, setAlerts] = useState({});
  const [expiringCerts, setExpiringCerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const daysOptions = [7, 15, 30, 60, 90];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Cargar usuarios
      const usersRes = await getAllUsers();
      setUsers(usersRes.data);

      // Cargar alertas para cada usuario
      const alertsMap = {};
      for (const user of usersRes.data) {
        const alertsRes = await getUserAlerts(user.id);
        alertsMap[user.id] = alertsRes.data;
      }
      setAlerts(alertsMap);

      // Verificar certificados próximos a vencer
      const expiringRes = await checkExpiringCertificates();
      setExpiringCerts(expiringRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
      Swal.fire('Error', 'Failed to load alerts data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAlert = async () => {
    if (!selectedUser) {
      Swal.fire('Warning', 'Please select a user', 'warning');
      return;
    }

    try {
      await createAlert({
        user_id: parseInt(selectedUser),
        days_before_expiration: daysBefore
      });
      
      Swal.fire('Success', 'Alert created successfully', 'success');
      loadData(); // Recargar datos
      setSelectedUser('');
    } catch (error) {
      Swal.fire('Error', 'Failed to create alert', 'error');
    }
  };

  const handleDeleteAlert = async (alertId) => {
    const result = await Swal.fire({
      title: 'Are you sure?',
      text: 'This alert will be deleted permanently',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      confirmButtonText: 'Yes, delete it!'
    });

    if (result.isConfirmed) {
      try {
        await deleteAlert(alertId);
        Swal.fire('Deleted!', 'Alert has been deleted.', 'success');
        loadData();
      } catch (error) {
        Swal.fire('Error', 'Failed to delete alert', 'error');
      }
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h2>Certificate Expiration Alerts</h2>

      {/* Sección de certificados próximos a vencer */}
      {expiringCerts.length > 0 && (
        <div className="alert alert-warning" style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#fff3cd', borderLeft: '4px solid #ffc107' }}>
          <h3>⚠️ Certificates Expiring Soon</h3>
          <table className="table">
            <thead>
              <tr>
                <th>User</th>
                <th>Days Until Expiry</th>
                <th>Expiry Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {expiringCerts.map(cert => (
                <tr key={cert.user_id}>
                  <td><strong>{cert.username}</strong></td>
                  <td style={{ color: cert.days_until_expiry <= 7 ? 'red' : 'orange' }}>
                    {cert.days_until_expiry} days
                  </td>
                  <td>{new Date(cert.expiry_date).toLocaleDateString()}</td>
                  <td>
                    <button 
                      onClick={() => window.open(`/users/${cert.user_id}`, '_blank')}
                      className="btn btn-sm btn-info"
                    >
                      View User
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Formulario para crear nuevas alertas */}
      <div className="card" style={{ marginBottom: '20px', padding: '20px' }}>
        <h3>Configure New Alert</h3>
        <div className="form-group">
          <label>Select User</label>
          <select 
            value={selectedUser} 
            onChange={(e) => setSelectedUser(e.target.value)}
            className="form-control"
          >
            <option value="">Select a user...</option>
            {users.map(user => (
              <option key={user.id} value={user.id}>
                {user.username} (Days: {user.cert_days})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Notify when certificate expires in:</label>
          <select 
            value={daysBefore} 
            onChange={(e) => setDaysBefore(parseInt(e.target.value))}
            className="form-control"
          >
            {daysOptions.map(days => (
              <option key={days} value={days}>{days} days</option>
            ))}
          </select>
        </div>

        <button onClick={handleCreateAlert} className="btn btn-primary">
          Create Alert
        </button>
      </div>

      {/* Lista de alertas existentes */}
      <h3>Configured Alerts</h3>
      <table className="table">
        <thead>
          <tr>
            <th>User</th>
            <th>Days Before Expiration</th>
            <th>Status</th>
            <th>Last Notified</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            alerts[user.id]?.map(alert => (
              <tr key={alert.id}>
                <td>{user.username}</td>
                <td>{alert.days_before_expiration} days</td>
                <td>
                  <span className={`badge ${alert.is_active ? 'badge-success' : 'badge-secondary'}`}>
                    {alert.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  {alert.last_notified_at 
                    ? new Date(alert.last_notified_at).toLocaleString()
                    : 'Never'
                  }
                </td>
                <td>
                  <button 
                    onClick={() => handleDeleteAlert(alert.id)}
                    className="btn btn-danger btn-sm"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CertificateAlertsPage;