import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import {
  Box,
  Button,
  Grid,
  TextField,
  Typography,
  Paper,
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCustomer, createCustomer, updateCustomer } from '../api/customers';

interface CustomerFormData {
  name: string;
  email: string;
  user_id: string;  // Add user_id field
  company?: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  notes?: string;
}

export default function CustomerForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEdit = !!id;

  const { register, handleSubmit, reset, formState: { errors } } = useForm<CustomerFormData>();

  const { data: customer } = useQuery({
    queryKey: ['customer', id],
    queryFn: () => getCustomer(id!),
    enabled: isEdit,
  });

  const createMutation = useMutation({
    mutationFn: createCustomer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      navigate('/customers');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: CustomerFormData }) =>
      updateCustomer(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      navigate('/customers');
    },
  });

  useEffect(() => {
    if (customer) {
      reset(customer);
    }
  }, [customer, reset]);

  const onSubmit = (data: CustomerFormData) => {
    if (isEdit) {
      updateMutation.mutate({ id, data });
    } else {
      // Set default user_id if not provided
      const customerData = {
        ...data,
        user_id: data.user_id || '00000000-0000-0000-0000-000000000000'
      };
      createMutation.mutate(customerData);
    }
  };

  return (
    <Paper sx={{ p: 4 }}>
      <Typography variant="h4" gutterBottom>
        {isEdit ? 'Edit Customer' : 'New Customer'}
      </Typography>
      <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
        <input 
          type="hidden" 
          {...register('user_id')} 
          defaultValue="00000000-0000-0000-0000-000000000000" 
        />
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <TextField
              required
              fullWidth
              label="Name"
              error={!!errors.name}
              helperText={errors.name?.message}
              {...register('name', { required: 'Name is required' })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              required
              fullWidth
              label="Email"
              type="email"
              error={!!errors.email}
              helperText={errors.email?.message}
              {...register('email', {
                required: 'Email is required',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Invalid email address',
                },
              })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Company"
              {...register('company')}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Phone"
              {...register('phone')}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Address"
              {...register('address')}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="City"
              {...register('city')}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="State"
              {...register('state')}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Postal Code"
              {...register('postal_code')}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Country"
              {...register('country')}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Notes"
              multiline
              rows={4}
              {...register('notes')}
            />
          </Grid>
        </Grid>
        <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            type="submit"
          >
            {isEdit ? 'Update' : 'Create'} Customer
          </Button>
          <Button
            variant="outlined"
            onClick={() => navigate('/customers')}
          >
            Cancel
          </Button>
        </Box>
      </Box>
    </Paper>
  );
} 