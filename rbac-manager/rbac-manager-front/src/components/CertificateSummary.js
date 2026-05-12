import React, { useState, useEffect } from 'react';
import { getExpiringCertificates } from '../services/certificateService';
import { Link } from 'react-router-dom';

const CertificateSummary = () => {
  const [summary, setSummary] = useState({
    critical: 0,
    warning: 0,
    attention: 0,
    total: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCertificateSummary();
    // Actualizar cada 30 segundos
    const interval = setInterval(fetchCertificateSummary, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchCertificateSummary = async () => {
    try {
      const response = await getExpiringCertificates();
      const certificates = response.data || [];
      
      const counts = {
        critical: certificates.filter(c => c.days_until_expiry <= 5 && c.days_until_expiry > 0).length,
        warning: certificates.filter(c => c.days_until_expiry > 5 && c.days_until_expiry <= 15).length,
        attention: certificates.filter(c => c.days_until_expiry > 15 && c.days_until_expiry <= 30).length,
        total: certificates.length
      };
      
      setSummary(counts);
    } catch (error) {
      console.error('Error fetching certificate summary:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="certificate-summary" style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
        <span style={{ fontSize: '12px', color: '#666' }}>Loading certs...</span>
      </div>
    );
  }

  if (summary.total === 0) {
    return (
      <div className="certificate-summary" style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
        <span style={{ fontSize: '12px', color: '#28a745' }}>✓ All certificates healthy</span>
      </div>
    );
  }

  return (
    <div className="certificate-summary" style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
      {summary.critical > 0 && (
        <Link to="/alerts" style={{ textDecoration: 'none' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            backgroundColor: '#dc3545',
            color: 'white',
            padding: '4px 10px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 'bold',
            textDecoration: 'none'
          }}>
            <span>🔴</span>
            <span>Critical: {summary.critical}</span>
          </div>
        </Link>
      )}
      
      {summary.warning > 0 && (
        <Link to="/alerts" style={{ textDecoration: 'none' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            backgroundColor: '#ffc107',
            color: '#856404',
            padding: '4px 10px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 'bold'
          }}>
            <span>🟡</span>
            <span>Warning: {summary.warning}</span>
          </div>
        </Link>
      )}
      
      {summary.attention > 0 && (
        <Link to="/alerts" style={{ textDecoration: 'none' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            backgroundColor: '#fd7e14',
            color: 'white',
            padding: '4px 10px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 'bold'
          }}>
            <span>🟠</span>
            <span>Attention: {summary.attention}</span>
          </div>
        </Link>
      )}
      
      {summary.total > 0 && (
        <Link to="/alerts" style={{ textDecoration: 'none' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            backgroundColor: '#6c757d',
            color: 'white',
            padding: '4px 10px',
            borderRadius: '20px',
            fontSize: '12px'
          }}>
            <span>📊</span>
            <span>Total: {summary.total}</span>
          </div>
        </Link>
      )}
    </div>
  );
};

export default CertificateSummary;