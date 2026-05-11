import React, { useState, useEffect } from 'react';
import { getAvailableApiResourcess } from '../../services/k8sService';
import { getAdditionalResources } from '../../services/profileService';
import Swal from 'sweetalert2';
import Autocomplete from '../Autocomplete';

const ManageProfilePermissionsModal = ({ currentPermissions = [], onClose, onSave }) => {
  const [permissions, setPermissions] = useState([]);
  const [newPermission, setNewPermission] = useState({
    resource: '',
    resource_api: null,
    resource_namespaced: true,
    is_verb_get: false,
    is_verb_list: false,
    is_verb_watch: false,
    is_verb_create: false,
    is_verb_update: false,
    is_verb_patch: false,
    is_verb_delete: false,
    is_verb_deletecollection: false
  });
  const [resourceOptions, setResourceOptions] = useState([]);

  useEffect(() => {
    const fetchResources = async () => {
      try {
        const apiResources = await getAvailableApiResourcess();
        // Normalize API resources to { resource, apiversion }
        const normalizedApiResources = apiResources.map(res => {
          const val = res.namespace;
          if (typeof val === 'object' && val !== null) {
            return {
              resource: val.resource,
              apiversion: val.apiversion || 'v1',
              namespaced: val.namespaced !== undefined ? val.namespaced : true
            };
          }
          return {
            resource: val,
            apiversion: 'v1',
            namespaced: true
          };
        });

        const manualResourcesResponse = await getAdditionalResources();
        const manualResources = manualResourcesResponse.data || [];

        // Merge and remove duplicates based on resource name AND apiversion
        const allResources = [...normalizedApiResources, ...manualResources];
        const uniqueResources = Array.from(new Map(allResources.map(item => [`${item.resource}-${item.apiversion}`, item])).values());

        setResourceOptions(uniqueResources);
      } catch (error) {
        console.error('Failed to fetch resource options:', error);
      }
    };
    fetchResources();
  }, []);

  useEffect(() => {
    const initialData = currentPermissions.length > 0 ? currentPermissions : [];
    setPermissions(initialData.map((p, i) => ({ ...p, local_id: p.id || `temp-${i}` })));
  }, [currentPermissions]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setNewPermission(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleResourceChange = (e) => {
    const { value, selectedOption } = e.target;

    // If selectedOption is provided (from Autocomplete selection), use it.
    // Otherwise, try to find it in the options (fallback for manual typing if exact match).
    // Note: With duplicates allowed by name, manual typing might be ambiguous, 
    // but Autocomplete selection is the primary way to disambiguate.
    let resourceData = selectedOption;

    if (!resourceData) {
      resourceData = resourceOptions.find(r => r.resource === value);
    }

    setNewPermission(prev => ({
      ...prev,
      resource: value,
      resource_api: resourceData ? resourceData.apiversion : null,
      resource_namespaced: resourceData ? resourceData.namespaced : true
    }));
  };

  const handleAddPermission = (e) => {
    e.preventDefault();
    if (newPermission.resource && !permissions.find(p => p.resource === newPermission.resource)) {
      setPermissions([...permissions, { ...newPermission, local_id: `temp-${Date.now()}` }]);
      setNewPermission({
        resource: '', resource_api: null, resource_namespaced: true,
        is_verb_get: false, is_verb_list: false, is_verb_watch: false,
        is_verb_create: false, is_verb_update: false, is_verb_patch: false,
        is_verb_delete: false, is_verb_deletecollection: false
      });
    } else {
      Swal.fire({ icon: 'warning', title: 'Invalid Permission', text: 'Resource cannot be empty or duplicated.' });
    }
  };

  const handleDeletePermission = (localIdToDelete) => {
    setPermissions(permissions.filter(p => p.local_id !== localIdToDelete));
  };

  const handleSave = () => {
    const permissionsToSave = permissions.map(({ local_id, ...rest }) => {
      // If fields are missing, try to find them in resourceOptions
      if (rest.resource_api === undefined || rest.resource_namespaced === undefined) {
        const match = resourceOptions.find(r => r.resource === rest.resource);
        if (match) {
          return {
            ...rest,
            resource_api: rest.resource_api || match.apiversion,
            resource_namespaced: rest.resource_namespaced !== undefined ? rest.resource_namespaced : match.namespaced
          };
        }
      }
      return rest;
    });
    onSave(permissionsToSave);
  };

  const verbKeys = [
    'is_verb_get', 'is_verb_list', 'is_verb_watch', 'is_verb_create',
    'is_verb_update', 'is_verb_patch', 'is_verb_delete', 'is_verb_deletecollection'
  ];

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
      backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000
    }}>
      <div style={{
        width: '95vw', maxWidth: '1100px', maxHeight: '90vh',
        display: 'flex', flexDirection: 'column', backgroundColor: 'white',
        borderRadius: '10px', overflow: 'hidden'
      }}>

        {/* Header */}
        <div style={{ padding: '15px 25px', borderBottom: '1px solid #ddd', flexShrink: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0 }}>Manage Permissions</h3>
          <button onClick={onClose} style={{ border: 'none', background: 'none', fontSize: '24px', cursor: 'pointer' }}>&times;</button>
        </div>

        {/* Form Container */}
        <div style={{ padding: '20px', backgroundColor: '#f9f9f9', borderBottom: '1px solid #eee', flexShrink: 0 }}>
          <form onSubmit={handleAddPermission} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Autocomplete
              name="resource"
              value={newPermission.resource}
              onChange={handleResourceChange}
              options={resourceOptions}
              placeholder="Search or select resource..."
            />

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {/* RESTAURADO: Select All Verbs */}
              <label style={{ fontWeight: 'bold', fontSize: '13px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={verbKeys.every(key => newPermission[key])}
                  onChange={(e) => {
                    const checked = e.target.checked;
                    setNewPermission(prev => {
                      const updated = { ...prev };
                      verbKeys.forEach(key => { updated[key] = checked; });
                      return updated;
                    });
                  }}
                /> Select All Verbs
              </label>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                {verbKeys.map(key => (
                  <label key={key} style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                    <input type="checkbox" name={key} checked={newPermission[key]} onChange={handleInputChange} />
                    {key.replace('is_verb_', '').toUpperCase()}
                  </label>
                ))}
              </div>
            </div>

            <button type="submit" style={{ alignSelf: 'center', padding: '8px 25px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
              Add Permission
            </button>
          </form>
        </div>

        {/* Main Scrollable Content (Table) */}
        <div style={{ flex: 1, overflow: 'auto', padding: '0 20px 20px 20px' }}>
          <h4 style={{ padding: '15px 0', margin: 0, backgroundColor: 'white', position: 'sticky', top: 0, zIndex: 11 }}>
            Current Permissions:
          </h4>

          {permissions.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0, minWidth: '900px' }}>
              <thead>
                <tr>
                  <th style={{ position: 'sticky', top: 0, backgroundColor: '#eeeeee', zIndex: 12, padding: '12px', textAlign: 'left', borderBottom: '2px solid #ccc' }}>Resource</th>
                  <th style={{ position: 'sticky', top: 0, backgroundColor: '#eeeeee', zIndex: 12, padding: '12px', textAlign: 'left', borderBottom: '2px solid #ccc' }}>API Group</th>
                  <th style={{ position: 'sticky', top: 0, backgroundColor: '#eeeeee', zIndex: 12, padding: '12px', textAlign: 'center', borderBottom: '2px solid #ccc' }}>Namespaced</th>
                  {verbKeys.map(k => (
                    <th key={k} style={{ position: 'sticky', top: 0, backgroundColor: '#eeeeee', zIndex: 12, padding: '12px', textAlign: 'center', borderBottom: '2px solid #ccc', fontSize: '11px' }}>
                      {k.replace('is_verb_', '').toUpperCase()}
                    </th>
                  ))}
                  <th style={{ position: 'sticky', top: 0, backgroundColor: '#eeeeee', zIndex: 12, padding: '12px', textAlign: 'center', borderBottom: '2px solid #ccc' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {permissions.map(perm => (
                  <tr key={perm.local_id}>
                    <td style={{ padding: '10px', borderBottom: '1px solid #eee', fontSize: '13px' }}>{perm.resource}</td>
                    <td style={{ padding: '10px', borderBottom: '1px solid #eee', fontSize: '13px' }}>{perm.resource_api || '-'}</td>
                    <td style={{ padding: '10px', borderBottom: '1px solid #eee', fontSize: '13px', textAlign: 'center' }}>{perm.resource_namespaced ? 'Yes' : 'No'}</td>
                    {verbKeys.map(k => (
                      <td key={k} style={{ textAlign: 'center', borderBottom: '1px solid #eee', fontSize: '16px' }}>
                        {perm[k] ? <span style={{ color: '#28a745' }}>&#10003;</span> : <span style={{ color: '#dc3545', opacity: 0.3 }}>&#10005;</span>}
                      </td>
                    ))}
                    <td style={{ textAlign: 'center', borderBottom: '1px solid #eee', padding: '5px' }}>
                      <button onClick={() => handleDeletePermission(perm.local_id)} style={{ backgroundColor: '#dc3545', color: 'white', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' }}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: '#666', fontStyle: 'italic' }}>No permissions defined.</p>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '15px 25px', borderTop: '1px solid #eee', flexShrink: 0, textAlign: 'right', backgroundColor: '#fff' }}>
          <button onClick={onClose} style={{ marginRight: '10px', padding: '8px 20px', border: '1px solid #ccc', background: '#f0f0f0', color: '#333', borderRadius: '5px', cursor: 'pointer' }}>Cancel</button>
          <button onClick={handleSave} style={{ padding: '8px 25px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold' }}>Save Changes</button>
        </div>
      </div>
    </div>
  );
};

export default ManageProfilePermissionsModal;

