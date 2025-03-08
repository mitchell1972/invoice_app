import React, { useState } from 'react';
import {
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Tooltip,
  Snackbar,
  Alert,
  Grid,
} from '@mui/material';
import {
  Add as AddIcon,
  Receipt as ReceiptIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCustomers, createCustomer, Customer } from '../api/customers';
import { createInvoice, CreateInvoiceData } from '../api/invoices';
import InvoiceFormModal from '../components/InvoiceFormModal';

interface NewCustomerForm {
  firstName: string;
  surname: string;
  email: string;
  tel: string;
  address: string;
  postcode: string;
  county: string;
}

export default function CustomerList() {
  const queryClient = useQueryClient();
  const [openDialog, setOpenDialog] = useState(false);
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [newCustomer, setNewCustomer] = useState<NewCustomerForm>({
    firstName: '',
    surname: '',
    email: '',
    tel: '',
    address: '',
    postcode: '',
    county: '',
  });

  // Track customers with invoices - store the id and status (for icon color)
  const [customerInvoices, setCustomerInvoices] = useState<{[key: string]: 'created' | 'saved'}>({});

  // State for invoice modal
  const [invoiceModalOpen, setInvoiceModalOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);

  const { data: customers = [], isLoading } = useQuery({
    queryKey: ['customers'],
    queryFn: getCustomers,
  });

  const createCustomerMutation = useMutation({
    mutationFn: createCustomer,
    onSuccess: (data) => {
      console.log('Customer created successfully:', data);
      queryClient.setQueryData(['customers'], (oldData: Customer[] = []) => [...oldData, data]);
      setSnackbarMessage(`Customer ${data.name} has been successfully created!`);
      setOpenSnackbar(true);
    },
    onError: (error: any) => {
      console.error('Mutation error:', error);
      if (error.response) {
        console.error('Server response:', {
          status: error.response.status,
          data: error.response.data,
          headers: error.response.headers
        });
      }
    }
  });

  const createInvoiceMutation = useMutation({
    mutationFn: createInvoice,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      setSnackbarMessage('Invoice has been successfully created!');
      setOpenSnackbar(true);

      // Mark the customer's invoice as saved (amber color)
      if (selectedCustomer) {
        setCustomerInvoices(prev => ({
          ...prev,
          [selectedCustomer.id]: 'saved'
        }));
      }
    },
  });

  // Function to open the invoice modal
  const handleOpenInvoiceModal = (customer: Customer) => {
    console.log('Opening invoice modal for customer:', customer.name);
    setSelectedCustomer(customer);
    setInvoiceModalOpen(true);
  };

  // Function to handle saving the invoice
  const handleSaveInvoice = async (invoiceData: CreateInvoiceData) => {
    console.log('Saving invoice:', invoiceData);
    await createInvoiceMutation.mutateAsync(invoiceData);
    setInvoiceModalOpen(false);
  };

  const handleCreateCustomer = async () => {
    if (!isFormValid()) return;

    // Map form fields to match the API's Customer interface
    const customerData = {
      name: `${newCustomer.firstName} ${newCustomer.surname}`,
      email: newCustomer.email,
      phone: newCustomer.tel,
      address: `${newCustomer.address}\n${newCustomer.postcode}`,  // Combine address components
      city: '',  // Could be added to form if needed
      state: newCustomer.county,
      postal_code: newCustomer.postcode,
      country: 'UK',
      company: '',  // Optional field
      notes: ''    // Optional field
    };

    try {
      console.log('Attempting to create customer with data:', customerData);
      await createCustomerMutation.mutateAsync(customerData);

      // Close dialog
      setOpenDialog(false);

      // Reset form
      setNewCustomer({
        firstName: '',
        surname: '',
        email: '',
        tel: '',
        address: '',
        postcode: '',
        county: '',
      });

      // Refresh customer list
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    } catch (error) {
      console.error('Failed to create customer:', error);
      alert(error instanceof Error ? error.message : 'Failed to create customer');
    }
  };

  const isFormValid = () => {
    return (
        newCustomer.firstName.trim() !== '' &&
        newCustomer.surname.trim() !== '' &&
        newCustomer.email.trim() !== '' &&
        newCustomer.tel.trim() !== '' &&
        newCustomer.address.trim() !== '' &&
        newCustomer.postcode.trim() !== '' &&
        newCustomer.county.trim() !== ''
    );
  };

  if (isLoading) {
    return <Typography>Loading...</Typography>;
  }

  return (
      <Box sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h4">Customers</Typography>
          <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setOpenDialog(true)}
          >
            Add Customer
          </Button>
        </Box>

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Phone</TableCell>
                <TableCell>Address</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {customers.map((customer) => (
                  <TableRow key={customer.id}>
                    <TableCell>{customer.name}</TableCell>
                    <TableCell>{customer.email}</TableCell>
                    <TableCell>{customer.phone || '-'}</TableCell>
                    <TableCell style={{ whiteSpace: 'pre-line' }}>{customer.address || '-'}</TableCell>
                    <TableCell align="right">
                      {customerInvoices[customer.id] === 'saved' ? (
                          <Tooltip title="Invoice Saved">
                            <IconButton color="warning">
                              <ReceiptIcon />
                            </IconButton>
                          </Tooltip>
                      ) : customerInvoices[customer.id] === 'created' ? (
                          <Tooltip title="Invoice Created">
                            <IconButton color="success">
                              <CheckIcon />
                            </IconButton>
                          </Tooltip>
                      ) : (
                          <Tooltip title="Create Invoice">
                            <IconButton
                                color="primary"
                                onClick={() => handleOpenInvoiceModal(customer)}
                            >
                              <ReceiptIcon />
                            </IconButton>
                          </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Customer Creation Dialog */}
        <Dialog
            open={openDialog}
            onClose={() => setOpenDialog(false)}
            maxWidth="sm"
            fullWidth
        >
          <DialogTitle>Add New Customer</DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                      label="First Name"
                      value={newCustomer.firstName}
                      onChange={(e) => setNewCustomer({ ...newCustomer, firstName: e.target.value })}
                      fullWidth
                      required
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                      label="Surname"
                      value={newCustomer.surname}
                      onChange={(e) => setNewCustomer({ ...newCustomer, surname: e.target.value })}
                      fullWidth
                      required
                  />
                </Grid>
              </Grid>
              <TextField
                  label="Email"
                  type="email"
                  value={newCustomer.email}
                  onChange={(e) => setNewCustomer({ ...newCustomer, email: e.target.value })}
                  fullWidth
                  required
              />
              <TextField
                  label="Telephone"
                  value={newCustomer.tel}
                  onChange={(e) => setNewCustomer({ ...newCustomer, tel: e.target.value })}
                  fullWidth
                  required
              />
              <TextField
                  label="Street Address"
                  value={newCustomer.address}
                  onChange={(e) => setNewCustomer({ ...newCustomer, address: e.target.value })}
                  fullWidth
                  required
                  multiline
                  rows={2}
              />
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                      label="Postcode"
                      value={newCustomer.postcode}
                      onChange={(e) => setNewCustomer({ ...newCustomer, postcode: e.target.value })}
                      fullWidth
                      required
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                      label="County"
                      value={newCustomer.county}
                      onChange={(e) => setNewCustomer({ ...newCustomer, county: e.target.value })}
                      fullWidth
                      required
                  />
                </Grid>
              </Grid>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
            <Button
                onClick={handleCreateCustomer}
                variant="contained"
                disabled={!isFormValid()}
            >
              Create
            </Button>
          </DialogActions>
        </Dialog>

        {/* Success Snackbar */}
        <Snackbar
            open={openSnackbar}
            autoHideDuration={6000}
            onClose={() => setOpenSnackbar(false)}
            anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert
              onClose={() => setOpenSnackbar(false)}
              severity="success"
              sx={{ width: '100%' }}
          >
            <Typography variant="subtitle1">
              {snackbarMessage}
            </Typography>
          </Alert>
        </Snackbar>

        {/* Invoice Form Modal - Make sure this is included */}
        <InvoiceFormModal
            open={invoiceModalOpen}
            onClose={() => setInvoiceModalOpen(false)}
            onSave={handleSaveInvoice}
            customer={selectedCustomer}
        />
      </Box>
  );
}