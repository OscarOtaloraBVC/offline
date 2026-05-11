import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import Swal from 'sweetalert2';

const UserForm = ({ onSubmit, defaultValues = {}, isEdit = false }) => {
  const { register, handleSubmit, reset, formState: { errors } } = useForm({ 
    defaultValues: {
      state: 'ENABLED',
      ...defaultValues
    }
  });

  useEffect(() => {
    if (defaultValues && Object.keys(defaultValues).length > 0) {
      reset({
        state: 'ENABLED',
        ...defaultValues
      });
    }
  }, [defaultValues, reset]);

  function isValidUsername(inputString) {
    if (typeof inputString !== 'string') return false;
    const processedString = inputString.trim().toLowerCase();
    if (processedString.length > 17) return false;
    const allowedCharsPattern = /^[a-z0-9_]*$/;
    if (!allowedCharsPattern.test(processedString)) return false;
    if (processedString.length > 0) {
      const purelyNumericPattern = /^[0-9]+$/;
      if (purelyNumericPattern.test(processedString)) return false;
    }
    return true;
  }

  const onSubmitProxy = (data) => {
    if (!isValidUsername(data.username)) {
      Swal.fire({
        icon: 'error',
        title: 'Invalid Username',
        text: 'The username does not meet the required format.',
      });
      return;
    }

    const filteredData = {
      username: data.username.trim().toLowerCase(),
      cert_days: Number(data.cert_days),
      observations: data.observations || "",
      state: data.state
    };

    onSubmit(filteredData); 
  };

  return (
    <form onSubmit={handleSubmit(onSubmitProxy)}>
      {/* Campo oculto para conservar el valor en el estado de la forma */}
      <input type="hidden" {...register('state')} />

      <div className="form-group">
        <label htmlFor="username">Username</label>
        <input
          id="username"
          type="text"
          {...register('username', { required: 'Username is required' })}
        />
        {errors.username && <p className="error-message">{errors.username.message}</p>}
      </div>

      <div className="form-group">
        <label>User Status</label>
        <div style={{ 
          padding: '10px', 
          backgroundColor: '#f4f4f4', 
          borderRadius: '4px', 
          border: '1px solid #ccc',
          color: '#666',
          fontWeight: 'bold',
          marginBottom: '10px'
        }}>
          {/* Mostramos el valor actual basado en defaultValues o el estado inicial */}
          {defaultValues.state || 'ENABLED'}
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="cert_days">Certificate Days</label>
        <input
          id="cert_days"
          type="number"
          {...register('cert_days', {
            required: 'Certificate days are required',
            valueAsNumber: true,
            min: { value: 1, message: 'Must be at least 1 day' }
          })}
        />
        {errors.cert_days && <p className="error-message">{errors.cert_days.message}</p>}
      </div>

      <div className="form-group">
        <label htmlFor="observations">Observations</label>
        <textarea
          id="observations"
          {...register('observations')}
        />
      </div>

      <button type="submit">{isEdit ? 'Update User' : 'Create User'}</button>
    </form>
  );
};

export default UserForm;
