// frontend/src/pages/alerts/CertificateAlertsPage.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  getGlobalAlert, 
  saveGlobalAlert, 
  deleteGlobalAlert 
} from '../../services/alertService';
import { getExpiringCertificates } from '../../services/certificateService';
import Swal from 'sweetalert2';

const CertificateAlertsPage = () => {
  const navigate = useNavigate();
  const [expiringCerts, setExpiringCerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [globalAlert, setGlobalAlert] = useState(null);
  const [notificationEmails, setNotificationEmails] = useState('');
  const [showValidationError, setShowValidationError] = useState(false);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      // Cargar certificados próximos a vencer
      const expiringRes = await getExpiringCertificates();
      setExpiringCerts(expiringRes.data || []);
      
      // Cargar configuración de alerta global
      const globalRes = await getGlobalAlert();
      const alert = globalRes.data;
      setGlobalAlert(alert);
      
      if (alert) {
        setNotificationEmails(alert.notification_emails || '');
      }
    } catch (error) {
      console.error('Error loading data:', error);
      Swal.fire('Error', 'Failed to load certificates data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfiguration = async () => {
    // Limpiar error visual previo
    setShowValidationError(false);
    
    // === NUEVA VALIDACIÓN: Verificar si ya existe una alerta ===
    if (globalAlert) {
      Swal.fire({
        icon: 'warning',
        title: 'Alert Already Exists',
        text: 'You already have a configured alert. Please delete the existing alert before creating a new one.',
        confirmButtonText: 'OK'
      });
      return;
    }

    // 1. Validar que haya emails
    if (!notificationEmails || !notificationEmails.trim()) {
      setShowValidationError(true);
      Swal.fire({
        icon: 'error',
        title: 'Email Required',
        text: 'Please enter at least one notification email address.',
        confirmButtonText: 'OK'
      });
      return;
    }

    // 2. Validar formato de emails
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const emails = notificationEmails.split(',').map(e => e.trim());
    
    // Filtrar emails vacíos
    const validEmails = emails.filter(e => e !== '');
    
    if (validEmails.length === 0) {
      setShowValidationError(true);
      Swal.fire({
        icon: 'error',
        title: 'Email Required',
        text: 'Please enter at least one valid email address.',
        confirmButtonText: 'OK'
      });
      return;
    }
    
    const invalidEmails = validEmails.filter(e => !emailRegex.test(e));
    
    if (invalidEmails.length > 0) {
      setShowValidationError(true);
      Swal.fire({
        icon: 'error',
        title: 'Invalid Email Format',
        html: `The following email(s) are invalid:<br/><strong>${invalidEmails.join(', ')}</strong><br/><br/>Please check the format.`,
        confirmButtonText: 'OK'
      });
      return;
    }

    try {
      const alertData = {
        days_before_expiration: 30,
        is_active: true,
        notification_emails: notificationEmails.trim()
      };
      
      await saveGlobalAlert(alertData);
      setShowValidationError(false);
      Swal.fire({
        icon: 'success',
        title: 'Success',
        text: 'Email configuration saved successfully',
        timer: 2000,
        showConfirmButton: false
      });
      await loadAllData();
    } catch (error) {
      console.error('Error saving configuration:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to save configuration';
      Swal.fire({
        icon: 'error',
        title: 'Error',
        text: errorMessage,
        confirmButtonText: 'OK'
      });
    }
  };

  const handleDeleteAlert = async (alert) => {
    const result = await Swal.fire({
      title: 'Delete Alert?',
      text: `Delete email report configuration for "${alert.notification_emails || 'No emails'}"? You can create a new one later.`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      confirmButtonText: 'Yes, delete'
    });

    if (result.isConfirmed) {
      try {
        await deleteGlobalAlert();
        Swal.fire('Deleted', 'Email report configuration has been deleted', 'success');
        await loadAllData();
      } catch (error) {
        console.error('Error deleting alert:', error);
        Swal.fire({
          icon: 'error',
          title: 'Error',
          text: error.response?.data?.detail || 'Failed to delete alert configuration',
          confirmButtonText: 'OK'
        });
      }
    }
  };
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
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
    if (days <= 5) return '#dc3545';
    if (days <= 15) return '#ffc107';
    if (days <= 30) return '#fd7e14';
    return '#28a745';
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
        <p>Loading certificate information...</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>🔐 Certificate Expiration Report</h2>
        <button onClick={handleRefresh} disabled={refreshing} className="btn btn-secondary">
          {refreshing ? 'Refreshing...' : '🔄 Refresh Status'}
        </button>
      </div>

      {/* SECCIÓN: CERTIFICADOS PRÓXIMOS A VENCER */}
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
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#ffe8a1' }}>
                  <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>User</th>
                  <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Status</th>
                  <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Days Remaining</th>
                  <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Expiration Date</th>
                  <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Certificate Days</th>
                  <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {expiringCerts.map(cert => (
                  <tr key={cert.user_id}>
                    <td style={{ padding: '10px', border: '1px solid #ddd' }}><strong>{cert.username}</strong></td>
                    <td style={{ padding: '10px', border: '1px solid #ddd' }}>
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
                    <td style={{ padding: '10px', border: '1px solid #ddd', color: getExpiryColor(cert.days_until_expiry), fontWeight: 'bold' }}>
                      {cert.days_until_expiry} days
                    </td>
                    <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                      {new Date(cert.expiry_date).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                      {cert.cert_days} days
                    </td>
                    <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                      <button
                        onClick={() => navigate(`/users/${cert.user_id}`)}
                        className="btn btn-sm btn-info"
                        style={{ padding: '5px 10px', fontSize: '12px', cursor: 'pointer' }}
                      >
                        👤 View User
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* SECCIÓN: CONFIGURAR NUEVA ALERTA*/}
      <div className="card" style={{ marginBottom: '30px', padding: '20px', backgroundColor: '#f8f9fa' }}>
        <h3>📧 Configure New Certificate Alert</h3>
        <p style={{ color: '#666', marginBottom: '15px' }}>
          Configure the email address(es) that will receive the complete certificate expiration report.
          The report will be sent automatically.<br /> 
          <br />
          <span style={{ color: '#dc3545', fontWeight: 'bold' }}>
          ⚠️ You can only have ONE active alert configuration at a time.
          </span><br />
        </p>
        
        <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ flex: 2, minWidth: '300px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Notification Emails (comma separated) <span style={{ color: '#dc3545' }}>*</span>
            </label>
            <input
              type="text"
              value={notificationEmails}
              onChange={(e) => setNotificationEmails(e.target.value)}
              placeholder="admin@example.com, team@example.com"
              className="form-control"
              style={{ 
                width: '90%', 
                padding: '8px', 
                border: '1px solid #ccc', 
                borderRadius: '4px',
                borderColor: !notificationEmails && showValidationError ? '#dc3545' : '#ccc'
              }}
              required
            />
            <small style={{ color: '#666', fontSize: '11px' }}>
              * Required. These recipients will receive the complete certificate report.
            </small>
          </div>
          
          <div>
            <button 
              onClick={handleSaveConfiguration} 
              className="btn btn-primary" 
              style={{ padding: '8px 24px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              ➕ Create Alert
            </button>
          </div>
        </div>
      </div>

      {/* SECCIÓN: ALERTAS CONFIGURADAS */}
      <div className="card" style={{ padding: '20px' }}>
        <h3>📋 Configured Alerts</h3>
        <p style={{ color: '#666', marginBottom: '15px' }}>
          Notification emails will receive the complete certificate expiration report 30 Days Before Exp.
        </p>
        {!globalAlert ? (
          <p style={{ textAlign: 'center', color: '#666', padding: '40px' }}>
            No alerts configured. Use the form above to create a certificate expiration alert.
          </p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#e9ecef' }}>

                  <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Notification Emails</th>

                  <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Last Notified</th>
                  <th style={{ padding: '12px', textAlign: 'center', border: '1px solid #ddd' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr>

                  <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                    {globalAlert.notification_emails ? (
                      <div>
                        {globalAlert.notification_emails.split(',').map((email, idx) => (
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

                  <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      backgroundColor: globalAlert.is_active ? '#d4edda' : '#f8d7da',
                      color: globalAlert.is_active ? '#155724' : '#721c24'
                    }}>
                      {globalAlert.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                    {globalAlert.last_notified_at 
                      ? new Date(globalAlert.last_notified_at).toLocaleString()
                      : 'Never notified'}
                  </td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center' }}>
                    <button
                      onClick={() => handleDeleteAlert(globalAlert)}
                      className="btn btn-danger btn-sm"
                      style={{ padding: '4px 12px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                    >
                      🗑️ Delete
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      {/* Información adicional */}
      <div className="card" style={{ marginTop: '20px', padding: '15px', backgroundColor: '#e7f3ff', borderLeft: '4px solid #2196F3' }}>
        <h4 style={{ margin: '0 0 10px 0' }}>ℹ️ How it works</h4>
        <p style={{ margin: 0, fontSize: '14px', color: '#555' }}>
          • The report includes ALL certificates shown in the "Certificates Expiring Soon" table above.<br />
          • Reports are automatically sent every 24 hours via Kubernetes CronJob.<br />
          <span style={{ color: '#dc3545', fontWeight: 'bold' }}>
          • ⚠️ You can only have ONE active alert configuration at a time.
          </span><br />
          • To change the email recipients, create a new alert (it will replace the existing one).
        </p>
      </div>
    </div>
  );
};

export default CertificateAlertsPage;