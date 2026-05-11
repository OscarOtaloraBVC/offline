import React, { useState, useEffect } from 'react';
import { getLastKubeconfig,reBuildtKubeconfig } from '../../services/k8sService';
import Swal from 'sweetalert2';

const ManageGetKubeconfigModal = ({ user, onClose }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [kubeconfigVal, setKubeconfigVal] = useState("");
  const [msgAlert, setMsgAlert] = useState("");

  useEffect(() => {
    const fetchKubeconfig = async () => {
      const kc = await getLastKubeconfig(user.id);
      setKubeconfigVal(kc.kubeconfig);
      setIsLoading(false);
      setMsgAlert("");
      if(kc.successful==false){
        setMsgAlert(kc.msg);
      }
    };
    fetchKubeconfig();

  }, []);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(kubeconfigVal);
    Swal.fire({
      icon: 'success',
      title: 'Copied!',
      text: 'Kubeconfig content copied to clipboard.',
      timer: 1500,
      showConfirmButton: false
    });
  };

  const handleBuildKubeconfig = async () => {
    const result = await Swal.fire({
      title: 'Are you sure?',
      text: 'This will invalidate the last kubeconfig generated for the user. Do you want to continue?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Yes, re-build it!'
    });

    if (result.isConfirmed) {
      setIsLoading(true);
      const kc = await reBuildtKubeconfig(user.id);
      setKubeconfigVal(kc.kubeconfig);
      setIsLoading(false);
      setMsgAlert("");
      if(kc.successful==false){
        setMsgAlert(kc.msg);
      } else {
        Swal.fire(
          'Re-built!',
          'A new kubeconfig has been generated.',
          'success'
        );
      }
    }

  };

  return (
    <div className="modal">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Get kubeconfig for: {user.username}</h3>
          <button onClick={onClose} className="close-button">×</button>
        </div>
        <div>
          <b style={{color:"red"}}>{msgAlert}</b>
          {isLoading ? (
            <div>
              <b>Loading...</b>
            </div>
          ) : (
            <div>

              <div style={{ border: '1px solid #eee', borderRadius: '4px', marginBottom: '1em' }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 12px',
                  backgroundColor: '#f7f7f7',
                  borderBottom: '1px solid #eee'
                }}>
                  <span>kubeconfig</span>
                  <button
                    onClick={handleCopy}
                    style={{
                      padding: '5px 10px',
                      fontSize: '0.9em',
                      cursor: 'pointer'
                    }}
                  >
                    Copy
                  </button>
                </div>
                <pre style={{
                  padding: '12px',
                  margin: '0',
                  overflowX: 'auto',
                  backgroundColor: '#fff',
                  fontFamily: 'monospace',
                  fontSize: '0.9em'
                }}>
                  <code>
                    {kubeconfigVal}
                  </code>
                </pre>
              </div>

              <br></br>
              <div align='center'>
                <button
                  onClick={() => handleBuildKubeconfig()}
                  className="danger"
                  style={{
                    padding: '5px 10px',
                    fontSize: '0.9em',
                    cursor: 'pointer'
                  }}
                >
                  Re-Build Kubeconfig
                </button>
              </div>

            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default ManageGetKubeconfigModal;