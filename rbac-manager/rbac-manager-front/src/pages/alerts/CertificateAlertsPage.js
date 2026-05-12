// frontend/src/pages/alerts/CertificateAlertsPage.js
import React, { useState, useEffect } from 'react';
import { getAllUsers } from '../../services/userService';
import { useNavigate } from 'react-router-dom';
import { getUserAlerts, createAlert, deleteAlert, notifyNow } from '../../services/alertService';
import { getExpiringCertificates } from '../../services/certificateService';  // 👈 CertificateService
import Swal from 'sweetalert2';

const CertificateAlertsPage = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedDays, setSelectedDays] = useState(5);
  const [notificationEmails, setNotificationEmails] = useState('');  // 👈 Notificacion Email
  const [userAlerts, setUserAlerts] = useState({});
  const [expiringCerts, setExpiringCerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const daysOptions = [5, 15, 30, 60, 90];
  useEffect(() => {
    loadAllData();
  }, []);
  const loadAllData = async () => {
    setLoading(true);
    try {
      // 1. Cargar usuarios
      const usersRes = await getAllUsers();
      const usersList = usersRes.data || [];
      setUsers(usersList);
      // 2. Cargar alertas por usuario
      const alertsMap = {};
      for (const user of usersList) {
        try {
          const alertsRes = await getUserAlerts(user.id);
          alertsMap[user.id] = alertsRes.data || [];
        } catch (err) {
          console.error(`Error loading alerts for user ${user.id}:`, err);
          alertsMap[user.id] = [];
        }
      }
      setUserAlerts(alertsMap);
      // 3. Cargar certificados próximos a vencer (dashboard - solo lectura)
      const expiringRes = await getExpiringCertificates();  // 👈 Certificates
      setExpiringCerts(expiringRes.data || []);
    } catch (error) {
      console.error('Error loading data:', error);
      Swal.fire('Error', 'Failed to load alerts data', 'error');
    } finally {
      setLoading(false);
    }
  };
  const handleCreateAlert = async () => {
    if (!selectedUserId) {
      Swal.fire('Warning', 'Please select a user', 'warning');
      return;
    }
    const selectedUser = users.find(u => u.id === parseInt(selectedUserId));
    // Validar emails si se ingresaron
    if (notificationEmails.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      const emails = notificationEmails.split(',').map(e => e.trim());
      const invalidEmails = emails.filter(e => e && !emailRegex.test(e));
      if (invalidEmails.length > 0) {
        Swal.fire('Error', `Invalid email(s): ${invalidEmails.join(', ')}`, 'error');
        return;
      }
    }
    try {
      await createAlert({
        user_id: parseInt(selectedUserId),
        days_before_expiration: selectedDays,
        notification_emails: notificationEmails.trim() || null  // 👈 Notificacion Email
      });
      
      Swal.fire('Success', `Alert created for user ${selectedUser?.username}`, 'success');
      await loadAllData();
      setSelectedUserId('');
      setSelectedDays(5);
      setNotificationEmails('');  // 👈 Limpiar emails      
    } catch (error) {
      console.error('Error creating alert:', error);
      Swal.fire('Error', error.response?.data?.detail || 'Failed to create alert', 'error');
    }
  };

  const handleDeleteAlert = async (alertId, userName) => {
    const result = await Swal.fire({
      title: 'Are you sure?',
      text: `Delete alert for user "${userName}"?`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      confirmButtonText: 'Yes, delete it!'
    });

    if (result.isConfirmed) {
      try {
        await deleteAlert(alertId);
        Swal.fire('Deleted!', 'Alert has been deleted.', 'success');
        await loadAllData();
      } catch (error) {
        Swal.fire('Error', 'Failed to delete alert', 'error');
      }
    }
  };

const handleNotifyNow = async (alertId, userName) => {
  const result = await Swal.fire({
    title: 'Send notification now?',
    text: `Send expiration alert for user "${userName}" immediately?`,
    icon: 'question',
    showCancelButton: true,
    confirmButtonColor: '#3085d6',
    cancelButtonColor: '#d33',
    confirmButtonText: 'Yes, send now!'
  });

  if (result.isConfirmed) {
    try {
      // Mostrar loading
      Swal.fire({
        title: 'Sending...',
        text: 'Please wait',
        allowOutsideClick: false,
        didOpen: () => {
          Swal.showLoading();
        }
      });

      const response = await notifyNow(alertId);
      
      // Recargar datos para actualizar last_notified_at
      await loadAllData();
      
      // Mostrar resultado
      if (response.data.email_sent) {
        Swal.fire({
          icon: 'success',
          title: 'Notification Sent!',
          html: `Email sent to:<br>${response.data.emails_sent_to.join('<br>')}`,
          timer: 3000,
          showConfirmButton: false
        });
      } else {
        Swal.fire({
          icon: 'warning',
          title: 'No Email Sent',
          text: 'No email addresses configured for this alert.',
          timer: 2000,
          showConfirmButton: false
        });
      }
    } catch (error) {
      console.error('Error sending notification:', error);
      Swal.fire({
        icon: 'error',
        title: 'Failed to Send',
        text: error.response?.data?.detail || 'Could not send notification'
      });
    }
  }
};  

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      // Solo recargar datos, no enviar notificaciones
      await loadAllData();
      Swal.fire('Refreshed', 'Certificate status updated', 'success');
    } catch (error) {
      console.error('Error refreshing:', error);
      Swal.fire('Error', 'Failed to refresh certificate status', 'error');
    } finally {
      setRefreshing(false);
    }
  };

  const getExpiryColor = (days) => {
    if (days <= 5) return '#dc3545';  // Rojo
    if (days <= 15) return '#ffc107'; // Amarillo
    if (days <= 30) return '#fd7e14'; // Naranja
    return '#28a745'; // Verde
  };

  const getExpiryStatus = (days) => {
    if (days <= 0) return 'EXPIRED';
    if (days <= 5) return 'Critical';
    if (days <= 15) return 'Warning';
    if (days <= 30) return 'Attention';
    return 'Healthy';
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="sr-only">Loading...</span>
        </div>
        <p>Loading certificate alerts...</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>🔐 Certificate Expiration Alerts</h2>
        <button onClick={handleRefresh} disabled={refreshing} className="btn btn-secondary">
          {refreshing ? 'Refreshing...' : '🔄 Refresh Status'}
        </button>
      </div>

      {/* SECCIÓN: CERTIFICADOS PRÓXIMOS A VENCER (DASHBOARD) */}
      <div className="card" style={{ marginBottom: '30px', padding: '20px', backgroundColor: '#fff3cd', borderLeft: '4px solid #ffc107' }}>
        <h3 style={{ marginTop: 0, color: '#856404' }}>
          ⚠️ Certificates Expiring Soon ({expiringCerts.length})
        </h3>
        
        {expiringCerts.length === 0 ? (
          <p style={{ color: '#28a745', margin: 0 }}>
            ✅ All certificates are healthy. No expiring certificates found.
          </p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#ffe8a1' }}>
                  <th style={{ padding: '12px', textAlign: 'left' }}>User</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Days Remaining</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Expiration Date</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Certificate Days</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {expiringCerts.map(cert => (
                  <tr key={cert.user_id} style={{ backgroundColor: cert.days_until_expiry <= 7 ? '#f8d7da' : 'transparent' }}>
                    <td style={{ padding: '10px' }}><strong>{cert.username}</strong></td>
                    <td style={{ padding: '10px' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        backgroundColor: getExpiryColor(cert.days_until_expiry),
                        color: '#fff'
                      }}>
                        {getExpiryStatus(cert.days_until_expiry)}
                      </span>
                    </td>
                    <td style={{ padding: '10px', color: getExpiryColor(cert.days_until_expiry), fontWeight: 'bold' }}>
                      {cert.days_until_expiry} days
                    </td>
                    <td style={{ padding: '10px' }}>
                      {new Date(cert.expiry_date).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '10px' }}>
                      {cert.cert_days} days
                    </td>
                    <td style={{ padding: '10px' }}>
                      <button
                        onClick={() => navigate(`/users/${cert.user_id}`)}
                        className="btn btn-sm btn-info"
                        style={{ marginRight: '8px' }}
                      >
                        👤 View User
                      </button>
                      <button
                        onClick={() => {
                          setSelectedUserId(cert.user_id.toString());
                          window.scrollTo({ top: 0, behavior: 'smooth' });
                        }}
                        className="btn btn-sm btn-warning"
                      >
                        🔔 Configure Alert
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* SECCIÓN: CONFIGURAR NUEVA ALERTA */}
      <div className="card" style={{ marginBottom: '30px', padding: '20px', backgroundColor: '#f8f9fa' }}>
        <h3>🔔 Configure New Certificate Alert</h3>
        <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ flex: 2, minWidth: '200px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Select User</label>
            <select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              className="form-control"
              style={{ width: '100%', padding: '8px' }}
            >
              <option value="">-- Select a user --</option>
              {users.map(user => (
                <option key={user.id} value={user.id}>
                  {user.username} (Cert: {user.cert_days} days)
                </option>
              ))}
            </select>
          </div>

          <div style={{ flex: 1, minWidth: '150px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Notify when expires in</label>
            <select
              value={selectedDays}
              onChange={(e) => setSelectedDays(parseInt(e.target.value))}
              className="form-control"
              style={{ width: '100%', padding: '8px' }}
            >
              {daysOptions.map(days => (
                <option key={days} value={days}>{days} days</option>
              ))}
            </select>
          </div>
          {/* 👈 NUEVO CAMPO DE EMAILS */}
          <div style={{ flex: 2, minWidth: '250px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Notification Emails (comma separated)
            </label>
            <input
              type="text"
              value={notificationEmails}
              onChange={(e) => setNotificationEmails(e.target.value)}
              placeholder="admin@example.com, team@example.com"
              className="form-control"
              style={{ width: '100%', padding: '8px' }}
            />
            <small style={{ color: '#666', fontSize: '11px' }}>
              Leave empty to skip email notifications
            </small>
          </div>
          <div>
            <button onClick={handleCreateAlert} className="btn btn-primary" style={{ padding: '8px 24px' }}>
              ➕ Create Alert
            </button>
          </div>
        </div>
      </div>

      {/* SECCIÓN: ALERTAS CONFIGURADAS */}
      <div className="card" style={{ padding: '20px' }}>
        <h3>📋 Configured Alerts</h3>
        
        {users.length === 0 ? (
          <p>No users found.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#e9ecef' }}>
                  <th style={{ padding: '12px', textAlign: 'left' }}>User</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Days Before Exp.</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Notification Emails</th>  {/* 👈 NUEVA COLUMNA */}
                  <th style={{ padding: '12px', textAlign: 'left' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Last Notified</th>
                  <th style={{ padding: '12px', textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(user => {
                  const alerts = userAlerts[user.id] || [];
                  if (alerts.length === 0) return null;
                  
                  return alerts.map(alert => (
                    <tr key={alert.id}>
                      <td style={{ padding: '10px' }}>
                        <strong>{user.username}</strong>
                        <br />
                        <small style={{ color: '#666' }}>ID: {user.id}</small>
                      </td>
                      <td style={{ padding: '10px', fontWeight: 'bold', color: '#0066cc' }}>
                        {alert.days_before_expiration} days
                      </td>

                      {/* CELDA DE EMAILS */}
                      <td style={{ padding: '10px' }}>
                        {alert.notification_emails ? (
                          <div style={{ fontSize: '12px' }}>
                            {alert.notification_emails.split(',').map((email, idx) => (
                              <span key={idx} style={{
                                display: 'inline-block',
                                backgroundColor: '#e9ecef',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                margin: '2px',
                                fontSize: '11px'
                              }}>
                                {email.trim()}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span style={{ color: '#999', fontSize: '12px' }}>No emails configured</span>
                        )}
                      </td>

                      <td style={{ padding: '10px' }}>
                        <span style={{
                          display: 'inline-block',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: 'bold',
                          backgroundColor: alert.is_active ? '#d4edda' : '#f8d7da',
                          color: alert.is_active ? '#155724' : '#721c24'
                        }}>
                          {alert.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td style={{ padding: '10px' }}>
                        {alert.last_notified_at 
                          ? new Date(alert.last_notified_at).toLocaleString()
                          : 'Never notified'}
                      </td>
                      <td style={{ padding: '10px', textAlign: 'center' }}>
                        
                        <button
                          onClick={() => handleNotifyNow(alert.id, user.username)}
                          className="btn btn-primary btn-sm"
                          style={{ 
                            padding: '4px 12px', 
                            marginRight: '8px',
                            backgroundColor: '#28a745',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                        >
                          📧 Notify Now
                        </button>
                        
                        
                        <button
                          onClick={() => handleDeleteAlert(alert.id, user.username)}
                          className="btn btn-danger btn-sm"
                          style={{ padding: '4px 12px' }}
                        >
                          🗑️ Delete
                        </button>
                      </td>
                    </tr>
                  ));
                })}
              </tbody>
            </table>
            
            {Object.values(userAlerts).every(alerts => alerts.length === 0) && (
              <p style={{ textAlign: 'center', color: '#666', padding: '40px' }}>
                No alerts configured. Use the form above to create certificate expiration alerts.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CertificateAlertsPage;