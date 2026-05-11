import React from 'react';
import { useForm } from 'react-hook-form';

const ProfileForm = ({ onSubmit, defaultValues = {}, isEdit = false }) => {
  const { register, handleSubmit, formState: { errors } } = useForm({ defaultValues });

  const profileTypes = [
    'OnlyReadOverAllCluster',
    'TotalAccessOverNamespace',
    'Customized',
    'SuperUsers'
  ];

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="form-group">
        <label htmlFor="name">Profile Name</label>
        <input
          id="name"
          type="text"
          {...register('name', { required: 'Profile name is required' })}
        />
        {errors.name && <p className="error-message">{errors.name.message}</p>}
      </div>

      <div className="form-group">
        <label htmlFor="type">Type</label>
        <select id="type" {...register('type', { required: 'Type is required' })} disabled={isEdit}>
          <option value="">Select a type...</option>
          {profileTypes.map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>
        {errors.type && <p className="error-message">{errors.type.message}</p>}
      </div>

      <button type="submit">{isEdit ? 'Update Profile' : 'Create Profile'}</button>
    </form>
  );
};

export default ProfileForm;