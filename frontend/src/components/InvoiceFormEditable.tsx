import React, { useState, useEffect } from 'react';
import {
    Box,
    Button,
    TextField,
    MenuItem,
    Grid,
    Paper,
    Typography,
    IconButton,
    InputAdornment,
    Snackbar,
    Alert,
    Divider,
    CircularProgress,
} from '@mui/material';
import {
    Add as AddIcon,
    Delete as DeleteIcon,
    ArrowBack as ArrowBackIcon,
    Save as SaveIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

interface InvoiceItem {
    id?: string;
    description: string;
    quantity: number;
    unit_price: number;
    total: number;
}

interface Customer {
    id: string;
    name: string;
    email: string;
    address?: string;
    city?: string;
    state?: string;
    postal_code?: string;
    country?: string;
    phone?: string;
}

interface Invoice {
    id: string;
    invoice_number: string;
    customer_id: string;
    user_id: string;
    issue_date: string;
    due_date: string;
    status: 'draft' | 'sent' | 'paid' | 'overdue' | 'reminder_sent' | 'cancelled';
    subtotal: number;
    tax: number;
    total: number;
    notes?: string;
    recipient_email?: string;
    currency_code?: string;
    items: InvoiceItem[];
    customer?: Customer;
}

const InvoiceFormEditable: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const [invoice, setInvoice] = useState<Invoice | null>(null);
    const [customer, setCustomer] = useState<Customer | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Form state
    const [invoiceNumber, setInvoiceNumber] = useState('');
    const [recipientEmail, setRecipientEmail] = useState('');
    const [issueDate, setIssueDate] = useState('');
    const [dueDate, setDueDate] = useState('');
    const [status, setStatus] = useState<string>('draft');
    const [currency, setCurrency] = useState('USD');
    const [notes, setNotes] = useState('');
    const [items, setItems] = useState<InvoiceItem[]>([]);

    // Calculated values
    const [subtotal, setSubtotal] = useState(0);
    const [taxRate, setTaxRate] = useState(20);
    const [tax, setTax] = useState(0);
    const [total, setTotal] = useState(0);

    // Currency options
    const currencies = [
        { code: 'USD', symbol: '$', name: 'US Dollar' },
        { code: 'GBP', symbol: '£', name: 'British Pound' },
        { code: 'EUR', symbol: '€', name: 'Euro' }
    ];

    // Status options
    const statusOptions = [
        { value: 'draft', label: 'Draft' },
        { value: 'sent', label: 'Sent' },
        { value: 'paid', label: 'Paid' },
        { value: 'overdue', label: 'Overdue' },
        { value: 'cancelled', label: 'Cancelled' }
    ];

    // Format date (YYYY-MM-DD)
    const formatDate = (dateString: string) => {
        try {
            const date = new Date(dateString);
            return date.toISOString().split('T')[0];
        } catch (e) {
            return '';
        }
    };

    // Load invoice data
    useEffect(() => {
        const fetchInvoice = async () => {
            try {
                setLoading(true);
                console.log(`Fetching invoice ${id}`);
                const response = await axios.get(`${API_URL}/invoices/${id}`);
                const invoiceData = response.data;
                console.log('Fetched invoice data:', invoiceData);

                setInvoice(invoiceData);
                setInvoiceNumber(invoiceData.invoice_number);
                setRecipientEmail(invoiceData.recipient_email || '');
                setIssueDate(formatDate(invoiceData.issue_date));
                setDueDate(formatDate(invoiceData.due_date));
                setStatus(invoiceData.status);
                setCurrency(invoiceData.currency_code || 'USD');
                setNotes(invoiceData.notes || '');

                // Set invoice items
                if (invoiceData.items && Array.isArray(invoiceData.items)) {
                    setItems(invoiceData.items.map((item: any) => ({
                        id: item.id,
                        description: item.description,
                        quantity: item.quantity,
                        unit_price: item.unit_price,
                        total: item.total
                    })));
                } else {
                    // Initialize with one empty item if no items
                    setItems([{
                        description: '',
                        quantity: 1,
                        unit_price: 0,
                        total: 0
                    }]);
                }

                // Set financial values
                setSubtotal(invoiceData.subtotal);
                setTax(invoiceData.tax);
                setTotal(invoiceData.total);
                setTaxRate(invoiceData.tax_rate || 20);

                // Fetch customer data
                if (invoiceData.customer_id) {
                    try {
                        const customerResponse = await axios.get(`${API_URL}/customers/${invoiceData.customer_id}`);
                        setCustomer(customerResponse.data);
                    } catch (err) {
                        console.error('Error fetching customer:', err);
                    }
                }
            } catch (err) {
                console.error('Error fetching invoice:', err);
                setError('Failed to load invoice data');
            } finally {
                setLoading(false);
            }
        };

        if (id) {
            fetchInvoice();
        }
    }, [id]);

    // Recalculate financials when items change
    useEffect(() => {
        const newSubtotal = items.reduce((sum, item) => sum + item.total, 0);
        setSubtotal(newSubtotal);

        const newTax = newSubtotal * (taxRate / 100);
        setTax(newTax);

        setTotal(newSubtotal + newTax);
    }, [items, taxRate]);

    // Handle item changes
    const handleItemChange = (index: number, field: keyof InvoiceItem, value: any) => {
        const updatedItems = [...items];
        updatedItems[index] = {
            ...updatedItems[index],
            [field]: value
        };

        // Recalculate total if quantity or unit_price changes
        if (field === 'quantity' || field === 'unit_price') {
            const qty = field === 'quantity' ? parseFloat(value) : updatedItems[index].quantity;
            const price = field === 'unit_price' ? parseFloat(value) : updatedItems[index].unit_price;
            updatedItems[index].total = qty * price;
        }

        setItems(updatedItems);
    };

    // Add new item
    const handleAddItem = () => {
        setItems([
            ...items,
            {
                description: '',
                quantity: 1,
                unit_price: 0,
                total: 0
            }
        ]);
    };

    // Remove item
    const handleRemoveItem = (index: number) => {
        if (items.length > 1) {
            const updatedItems = [...items];
            updatedItems.splice(index, 1);
            setItems(updatedItems);
        }
    };

    // Handle save
    const handleSave = async () => {
        try {
            setSaving(true);
            setError(null);

            // Validate required fields
            if (!invoiceNumber || !issueDate || !dueDate) {
                setError('Please fill in all required fields');
                setSaving(false);
                return;
            }

            // Validate items
            if (items.length === 0 || items.some(item => !item.description)) {
                setError('Please add at least one valid item with description');
                setSaving(false);
                return;
            }

            // Prepare data for update
            const updateData = {
                invoice_number: invoiceNumber,
                recipient_email: recipientEmail,
                issue_date: new Date(issueDate).toISOString(),
                due_date: new Date(dueDate).toISOString(),
                status,
                currency_code: currency,
                notes,
                subtotal,
                tax,
                tax_rate: taxRate,
                total,
                items: items.map(({ id, ...item }) => item) // Remove id to use backend-generated ids
            };

            console.log('Updating invoice with data:', updateData);

            // Send update request
            const response = await axios.put(`${API_URL}/invoices/${id}`, updateData);
            console.log('Update response:', response.data);

            setSuccess(true);

            // Navigate back to invoices list after delay
            setTimeout(() => {
                navigate('/invoices');
            }, 1500);
        } catch (err: any) {
            console.error('Error saving invoice:', err);

            let errorMessage = 'Failed to update invoice';
            if (err.response && err.response.data && err.response.data.detail) {
                errorMessage = err.response.data.detail;
            }
            setError(errorMessage);
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Button
                    startIcon={<ArrowBackIcon />}
                    onClick={() => navigate('/invoices')}
                >
                    Back to Invoices
                </Button>
                <Typography variant="h4">Edit Invoice #{invoiceNumber}</Typography>
            </Box>

            <Paper sx={{ p: 3 }}>
                {customer && (
                    <Box sx={{ mb: 4 }}>
                        <Typography variant="h6" gutterBottom>Customer Information</Typography>
                        <Grid container spacing={2}>
                            <Grid item xs={12} md={6}>
                                <Typography variant="subtitle2" color="textSecondary">
                                    Bill To:
                                </Typography>
                                <Typography variant="body1">
                                    <strong>{customer.name}</strong>
                                </Typography>
                                <Typography variant="body2" component="div" style={{ whiteSpace: 'pre-line' }}>
                                    {customer.address}
                                    {customer.city && <br />}
                                    {customer.city} {customer.state} {customer.postal_code}
                                    {customer.country && <br />}
                                    {customer.country}
                                </Typography>
                                <Typography variant="body2" sx={{ mt: 1 }}>
                                    {customer.phone}
                                </Typography>
                            </Grid>
                        </Grid>
                    </Box>
                )}

                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            label="Invoice Number"
                            value={invoiceNumber}
                            onChange={(e) => setInvoiceNumber(e.target.value)}
                            fullWidth
                            required
                        />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <TextField
                            label="Recipient Email"
                            type="email"
                            value={recipientEmail}
                            onChange={(e) => setRecipientEmail(e.target.value)}
                            fullWidth
                            placeholder="email@example.com"
                        />
                    </Grid>

                    <Grid item xs={12} sm={4}>
                        <TextField
                            label="Issue Date"
                            type="date"
                            value={issueDate}
                            onChange={(e) => setIssueDate(e.target.value)}
                            fullWidth
                            required
                            InputLabelProps={{
                                shrink: true,
                            }}
                        />
                    </Grid>

                    <Grid item xs={12} sm={4}>
                        <TextField
                            label="Due Date"
                            type="date"
                            value={dueDate}
                            onChange={(e) => setDueDate(e.target.value)}
                            fullWidth
                            required
                            InputLabelProps={{
                                shrink: true,
                            }}
                        />
                    </Grid>

                    <Grid item xs={12} sm={4}>
                        <TextField
                            select
                            label="Currency"
                            value={currency}
                            onChange={(e) => setCurrency(e.target.value)}
                            fullWidth
                        >
                            {currencies.map((option) => (
                                <MenuItem key={option.code} value={option.code}>
                                    {option.symbol} - {option.name}
                                </MenuItem>
                            ))}
                        </TextField>
                    </Grid>

                    <Grid item xs={12}>
                        <TextField
                            select
                            label="Status"
                            value={status}
                            onChange={(e) => setStatus(e.target.value)}
                            fullWidth
                        >
                            {statusOptions.map((option) => (
                                <MenuItem key={option.value} value={option.value}>
                                    {option.label}
                                </MenuItem>
                            ))}
                        </TextField>
                    </Grid>
                </Grid>

                <Box sx={{ mt: 4 }}>
                    <Typography variant="h6" gutterBottom>
                        Invoice Items
                    </Typography>

                    <Divider sx={{ mb: 2 }} />

                    {items.map((item, index) => (
                        <Grid container spacing={2} key={index} sx={{ mb: 2 }}>
                            <Grid item xs={12} sm={5}>
                                <TextField
                                    label="Description"
                                    value={item.description}
                                    onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                                    fullWidth
                                    required
                                />
                            </Grid>

                            <Grid item xs={6} sm={2}>
                                <TextField
                                    label="Quantity"
                                    type="number"
                                    value={item.quantity}
                                    onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                                    fullWidth
                                    required
                                    InputProps={{
                                        inputProps: { min: 1, step: 0.01 }
                                    }}
                                />
                            </Grid>

                            <Grid item xs={6} sm={2}>
                                <TextField
                                    label="Unit Price"
                                    type="number"
                                    value={item.unit_price}
                                    onChange={(e) => handleItemChange(index, 'unit_price', e.target.value)}
                                    fullWidth
                                    required
                                    InputProps={{
                                        startAdornment: <InputAdornment position="start">
                                            {currencies.find(c => c.code === currency)?.symbol || '$'}
                                        </InputAdornment>,
                                        inputProps: { min: 0, step: 0.01 }
                                    }}
                                />
                            </Grid>

                            <Grid item xs={10} sm={2}>
                                <TextField
                                    label="Total"
                                    type="number"
                                    value={item.total.toFixed(2)}
                                    InputProps={{
                                        startAdornment: <InputAdornment position="start">
                                            {currencies.find(c => c.code === currency)?.symbol || '$'}
                                        </InputAdornment>,
                                        readOnly: true
                                    }}
                                    fullWidth
                                />
                            </Grid>

                            <Grid item xs={2} sm={1} sx={{ display: 'flex', alignItems: 'center' }}>
                                <IconButton
                                    color="error"
                                    onClick={() => handleRemoveItem(index)}
                                    disabled={items.length === 1}
                                >
                                    <DeleteIcon />
                                </IconButton>
                            </Grid>
                        </Grid>
                    ))}

                    <Button
                        startIcon={<AddIcon />}
                        onClick={handleAddItem}
                        variant="outlined"
                        sx={{ mt: 1 }}
                    >
                        Add Item
                    </Button>
                </Box>

                <Box sx={{ mt: 4, bgcolor: 'grey.100', p: 2, borderRadius: 1 }}>
                    <Grid container spacing={2}>
                        <Grid item xs={6} sm={9} />
                        <Grid item xs={6} sm={3}>
                            <Box sx={{ mb: 1 }}>
                                <TextField
                                    label="Subtotal"
                                    type="number"
                                    value={subtotal.toFixed(2)}
                                    InputProps={{
                                        startAdornment: <InputAdornment position="start">
                                            {currencies.find(c => c.code === currency)?.symbol || '$'}
                                        </InputAdornment>,
                                        readOnly: true
                                    }}
                                    fullWidth
                                />
                            </Box>

                            <Grid container spacing={1}>
                                <Grid item xs={4}>
                                    <TextField
                                        label="Tax Rate"
                                        type="number"
                                        value={taxRate}
                                        onChange={(e) => setTaxRate(parseFloat(e.target.value) || 0)}
                                        InputProps={{
                                            endAdornment: <InputAdornment position="end">%</InputAdornment>,
                                            inputProps: { min: 0, max: 100, step: 0.5 }
                                        }}
                                        fullWidth
                                    />
                                </Grid>
                                <Grid item xs={8}>
                                    <TextField
                                        label="Tax Amount"
                                        type="number"
                                        value={tax.toFixed(2)}
                                        InputProps={{
                                            startAdornment: <InputAdornment position="start">
                                                {currencies.find(c => c.code === currency)?.symbol || '$'}
                                            </InputAdornment>,
                                            readOnly: true
                                        }}
                                        fullWidth
                                    />
                                </Grid>
                            </Grid>

                            <Divider sx={{ my: 1 }} />

                            <TextField
                                label="Total"
                                type="number"
                                value={total.toFixed(2)}
                                InputProps={{
                                    startAdornment: <InputAdornment position="start">
                                        {currencies.find(c => c.code === currency)?.symbol || '$'}
                                    </InputAdornment>,
                                    readOnly: true
                                }}
                                fullWidth
                                sx={{ mt: 1 }}
                            />
                        </Grid>
                    </Grid>
                </Box>

                <Box sx={{ mt: 3 }}>
                    <TextField
                        label="Notes"
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        fullWidth
                        multiline
                        rows={3}
                    />
                </Box>

                <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                    <Button
                        variant="outlined"
                        onClick={() => navigate('/invoices')}
                    >
                        Cancel
                    </Button>
                    <Button
                        variant="contained"
                        color="primary"
                        startIcon={<SaveIcon />}
                        onClick={handleSave}
                        disabled={saving}
                    >
                        {saving ? 'Saving...' : 'Save Changes'}
                    </Button>
                </Box>
            </Paper>

            {/* Success Message */}
            <Snackbar
                open={success}
                autoHideDuration={3000}
                onClose={() => setSuccess(false)}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert severity="success" elevation={6} variant="filled">
                    Invoice updated successfully!
                </Alert>
            </Snackbar>

            {/* Error Message */}
            <Snackbar
                open={!!error}
                autoHideDuration={5000}
                onClose={() => setError(null)}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert severity="error" elevation={6} variant="filled">
                    {error}
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default InvoiceFormEditable;