import React, { useState, useEffect } from 'react';
import { getAvailableNamespaces } from '../../services/k8sService';
import Swal from 'sweetalert2';

const ManageUserAssignmentsModal = ({ currentUserAssignments = [], allProfiles = [], onClose, onSave }) => {
  const [assignments, setAssignments] = useState([]);
  const [newAssignment, setNewAssignment] = useState({ profile_id: '', namespace: '' });
  const [selectedProfileType, setSelectedProfileType] = useState(null);
  
  const [allSystemNamespaces, setAllSystemNamespaces] = useState([]);
  const [loading, setLoading] = useState(true);

  /**
   * Identifica si un tipo de perfil es a nivel de todo el cluster.
   * Se agregÃ³ 'SuperUsers' a la lista para que herede el comportamiento global.
   */
  const isClusterWideType = (type) => {
    const globalRoles = ['OnlyReadOverAllCluster', 'SuperUser', 'SuperUsers'];
    return globalRoles.includes(type);
  };

  useEffect(() => {
    const initialAssignments = currentUserAssignments.map(a => ({
      profile_id: a.profile.id,
      profile_name: a.profile.name,
      namespace: a.namespace,
    }));
    setAssignments(initialAssignments);
  }, [currentUserAssignments]);

  useEffect(() => {
    const fetchNamespaces = async () => {
      setLoading(true);
      try {
        const fetchedNs = await getAvailableNamespaces();
        setAllSystemNamespaces(fetchedNs || []);
      } catch (error) {
        console.error("Failed to fetch namespaces:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchNamespaces();
  }, []);

  const handleProfileChange = (e) => {
    const profileId = e.target.value;
    const profile = allProfiles.find(p => p.id === parseInt(profileId));
    const profileType = profile ? profile.type : null;

    setSelectedProfileType(profileType);

    // Si el perfil es de cluster (incluyendo SuperUsers), reseteamos el namespace a vacÃ­o
    setNewAssignment({ profile_id: profileId, namespace: '' });
  };

  const handleAddAssignment = (e) => {
    e.preventDefault();
    const { profile_id, namespace } = newAssignment;

    if (!profile_id) {
      Swal.fire({
        icon: 'warning',
        title: 'Incomplete Selection',
        text: 'Please select a profile.',
      });
      return;
    }

    const needsNamespace = !isClusterWideType(selectedProfileType);

    if (needsNamespace && !namespace) {
      Swal.fire({
        icon: 'warning',
        title: 'Namespace Required',
        text: 'A namespace is required for this profile type.',
      });
      return;
    }

    // Si es tipo cluster/global, el namespace final debe ser null
    const finalNamespace = needsNamespace ? namespace : null;

    const isDuplicate = assignments.some(
      a => a.profile_id === parseInt(profile_id) && a.namespace === finalNamespace
    );

    if (isDuplicate) {
      Swal.fire({
        icon: 'warning',
        title: 'Duplicate Assignment',
        text: `This assignment already exists.`,
      });
      return;
    }
    
    const profile = allProfiles.find(p => p.id === parseInt(profile_id));

    setAssignments([
      ...assignments, 
      { 
        profile_id: parseInt(profile_id), 
        profile_name: profile.name, 
        namespace: finalNamespace 
      }
    ]);

    setNewAssignment({ profile_id: '', namespace: '' });
    setSelectedProfileType(null);
  };

  const handleDeleteAssignment = (indexToDelete) => {
    setAssignments(assignments.filter((_, index) => index !== indexToDelete));
  };

  const handleSave = () => {
    const assignmentsToSave = assignments.map(({ profile_id, namespace }) => ({
      profile_id,
      namespace: namespace,
    }));
    onSave(assignmentsToSave);
  };

  if (loading) {
    return (
      <div className="modal"><div className="modal-content"><p>Loading namespaces...</p></div></div>
    );
  }

  return (
    <div className="modal">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Manage Profile & Namespace Assignments</h3>
          <button onClick={onClose} className="close-button">Ã</button>
        </div>

        <form onSubmit={handleAddAssignment} className="add-item-form">
          {/* Selector de Perfil */}
          <select value={newAssignment.profile_id} onChange={handleProfileChange}>
            <option value="">-- Select a Profile --</option>
            {allProfiles.map(p => (
              <option key={p.id} value={p.id}>{p.name} ({p.type})</option>
            ))}
          </select>

          {/* Selector de Namespace: Deshabilitado si es SuperUsers, SuperUser o OnlyReadOverAllCluster */}
          <select 
            value={newAssignment.namespace} 
            disabled={isClusterWideType(selectedProfileType)} 
            onChange={(e) => setNewAssignment({ ...newAssignment, namespace: e.target.value })}
          >
            <option value="">
              {isClusterWideType(selectedProfileType) ? '-- Not required for this profile --' : '-- Select a Namespace --'}
            </option>
            {allSystemNamespaces.map(ns => (
              <option key={ns.namespace} value={ns.namespace}>{ns.namespace}</option>
            ))}
          </select>

          <button type="submit">Add Assignment</button>
        </form>

        <div className="list-management" style={{ maxHeight: "300px", overflow: "auto" }}>
          <h4>Current Assignments:</h4>
          {assignments.length > 0 ? (
            <ul>
              {assignments.map((a, index) => (
                <li key={`${a.profile_id}-${a.namespace}-${index}`}>
                  <span className="badge">
                    {a.namespace || 'Cluster-wide'}
                  </span>
                  {' / '}
                  <strong>{a.profile_name}</strong>
                  <button 
                    onClick={() => handleDeleteAssignment(index)} 
                    className="danger" 
                    style={{ marginLeft: '10px', padding: '3px 8px', fontSize: '0.8em' }}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          ) : (<p>No assignments defined.</p>)}
        </div>

        <div style={{ marginTop: '20px', textAlign: 'right' }}>
          <button onClick={onClose} className="secondary" style={{ marginRight: '10px' }}>Cancel</button>
          <button onClick={handleSave} className="primary">Save Changes</button>
        </div>
      </div>
    </div>
  );
};

export default ManageUserAssignmentsModal;