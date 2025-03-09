import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Box,
    Button,
    Paper,
    Typography,
    Grid,
    TextField,
    MenuItem,
    InputAdornment,
    IconButton,
    Snackbar,
    Alert,
    Divider,
    CircularProgress,
    FormControl,
    InputLabel,
    Select,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon, ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getInvoice, updateInvoice, Invoice } from '../api/invoices';
import { getCustomer } from '../api/customers';

interface InvoiceItem {
    id: string;
    description: string;
    quantity: number;
    unit_price: number;
    total: number;
}

type Currency = {
    code: string;
    symbol: string;
    name: string;
};

const InvoiceForm = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    
    // States for invoice data
    const [invoiceNumber, setInvoiceNumber] = useState('');
    const [issueDate, setIssueDate] = useState<Date>(new Date());
    const [dueDate, setDueDate] = useState<Date>(new Date());
    const [status, setStatus] = useState<'draft' | 'sent' | 'paid' | 'overdue' | 'reminder_sent' | 'cancelled'>('draft');
    const [notes, setNotes] = useState('');
    const [recipientEmail, setRecipientEmail] = useState('');
    const [currency, setCurrency] = useState<Currency>({ code: 'USD', symbol: '$', name: 'US Dollar' });
    const [items, setItems] = useState<InvoiceItem[]>([]);
    const [customerId, setCustomerId] = useState('');
    const [userId, setUserId] = useState('');
    const [taxRate, setTaxRate] = useState<number>(20); // Make tax rate editable
    
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showSuccessMessage, setShowSuccessMessage] = useState(false);
    
    // Available currencies
    const currencies: Currency[] = [
        { code: 'USD', symbol: '$', name: 'US Dollar' },
        { code: 'GBP', symbol: '£', name: 'British Pound' },
        { code: 'EUR', symbol: '€', name: 'Euro' }
    ];
    
    // Format date for display in the date picker (YYYY-MM-DD format)
    const formatDateForPicker = (date: Date): string => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    // Format date as ISO string for API
    const formatDateToISOString = (date: Date): string => {
        return date.toISOString();
    };
    
    // Format currency display
    const formatCurrency = (amount: number): string => {
        return `${currency.symbol} ${amount.toFixed(2)}`;
    };
    
    // Calculate totals (use state to allow manual overrides)
    const [manualSubtotal, setManualSubtotal] = useState<number | null>(null);
    const [manualTotal, setManualTotal] = useState<number | null>(null);
    
    // Calculate based on items or use manual override
    const calculatedSubtotal = items.reduce((sum, item) => sum + item.total, 0);
    const subtotal = manualSubtotal !== null ? manualSubtotal : calculatedSubtotal;
    const taxAmount = subtotal * (taxRate / 100);
    const calculatedTotal = subtotal + taxAmount;
    const total = manualTotal !== null ? manualTotal : calculatedTotal;
    
    // Fetch invoice data
    const { data: invoice, isLoading: isInvoiceLoading } = useQuery({
        queryKey: ['invoice', id],
        queryFn: () => getInvoice(id!),
        enabled: !!id
    });
    
    // Use useEffect to update form fields when invoice data is loaded
    useEffect(() => {
        if (invoice) {
            // Fill in the form with the invoice data
            setInvoiceNumber(invoice.invoice_number);
            setIssueDate(new Date(invoice.issue_date));
            setDueDate(new Date(invoice.due_date));
            setStatus(invoice.status as any);
            setNotes(invoice.notes || '');
            setRecipientEmail(invoice.recipient_email || '');
            
            // Set tax rate if available, otherwise calculate it from subtotal and tax
            if (invoice.tax_rate !== undefined) {
                setTaxRate(invoice.tax_rate);
            } else if (invoice.subtotal > 0 && invoice.tax > 0) {
                setTaxRate((invoice.tax / invoice.subtotal) * 100);
            }
            
            // Set currency
            setCurrency(
                currencies.find(c => c.code === invoice.currency_code) || 
                { code: invoice.currency_code || 'USD', symbol: '$', name: 'US Dollar' }
            );
            
            // Set items
            setItems(invoice.items.map((item: any, index: number) => ({
                id: String(index + 1),
                description: item.description,
                quantity: item.quantity,
                unit_price: item.unit_price,
                total: item.total
            })));
            
            // Set customer and user IDs
            setCustomerId(invoice.customer_id);
            setUserId(invoice.user_id);
            
            // Set subtotal and total for manual override if they don't match calculated values
            const itemsTotal = invoice.items.reduce((sum: number, item: any) => sum + item.total, 0);
            if (Math.abs(itemsTotal - invoice.subtotal) > 0.01) {
                setManualSubtotal(invoice.subtotal);
            }
            
            const calculatedTotal = invoice.subtotal + invoice.tax;
            if (Math.abs(calculatedTotal - invoice.total) > 0.01) {
                setManualTotal(invoice.total);
            }
        }
    }, [invoice, currencies]);
    
    // Fetch customer data based on customer_id from invoice
    const { data: customer } = useQuery({
        queryKey: ['customer', customerId],
        queryFn: () => getCustomer(customerId),
        enabled: !!customerId,
    });
    
    // Update invoice mutation
    const updateInvoiceMutation = useMutation({
        mutationFn: ({id, data}: {id: string, data: any}) => updateInvoice(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['invoices'] });
            queryClient.invalidateQueries({ queryKey: ['invoice', id] });
            setShowSuccessMessage(true);
        }
    });
    
    const handleAddItem = () => {
        setItems([
            ...items,
            {
                id: Date.now().toString(),
                description: '',
                quantity: 1,
                unit_price: 0,
                total: 0
            }
        ]);
    };
    
    const handleRemoveItem = (id: string) => {
        if (items.length > 1) {
            setItems(items.filter(item => item.id !== id));
        }
    };
    
    const handleItemChange = (id: string, field: keyof InvoiceItem, value: string | number) => {
        setItems(
            items.map(item => {
                if (item.id === id) {
                    const updatedItem = { ...item, [field]: value };
                    
                    // Recalculate total if quantity or unit_price changes
                    if (field === 'quantity' || field === 'unit_price') {
                        updatedItem.quantity = typeof updatedItem.quantity === 'string'
                            ? parseFloat(updatedItem.quantity)
                            : updatedItem.quantity;
                        
                        updatedItem.unit_price = typeof updatedItem.unit_price === 'string'
                            ? parseFloat(updatedItem.unit_price)
                            : updatedItem.unit_price;
                        
                        updatedItem.total = updatedItem.quantity * updatedItem.unit_price;
                    }
                    
                    return updatedItem;
                }
                return item;
            })
        );
    };
    
    const handleSubmit = async () => {
        // Validate that at least one item exists and has required fields
        if (items.length === 0 || items.some(item => !item.description || item.quantity <= 0)) {
            alert('Please add at least one valid item with description and quantity');
            return;
        }
        
        setIsSubmitting(true);
        
        try {
            // Ensure all items have valid data
            const validItems = items.map(({ id, ...item }) => ({
                description: item.description || 'Service',
                quantity: item.quantity || 1,
                unit_price: item.unit_price || 0,
                total: item.total || 0
            }));
            
            // Create a copy of the dates to ensure consistent handling
            const issueDateTime = new Date(issueDate);
            const dueDateTime = new Date(dueDate);
            
            // Create the update data
            const invoiceData = {
                invoice_number: invoiceNumber,
                issue_date: formatDateToISOString(issueDateTime),
                due_date: formatDateToISOString(dueDateTime),
                status,
                subtotal,
                tax: taxAmount,
                tax_rate: taxRate,  // Save the tax rate
                total,
                notes,
                recipient_email: recipientEmail,
                currency_code: currency.code,
                items: validItems
            };
            
            await updateInvoiceMutation.mutateAsync({ id: id!, data: invoiceData });
            
            // Show success message immediately
            setShowSuccessMessage(true);
            
            // Navigate back to invoices list after a delay
            setTimeout(() => {
                navigate('/invoices');
            }, 1500);
        } catch (error) {
            console.error('Error updating invoice:', error);
            alert('Failed to update invoice. Please check all required fields and try again.');
        } finally {
            setIsSubmitting(false);
        }
    };
    
    if (isInvoiceLoading) {
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
                            required
                            placeholder="email@example.com"
                        />
                    </Grid>
                    
                    <Grid item xs={12} sm={4}>
                        <TextField
                            label="Issue Date"
                            type="date"
                            value={formatDateForPicker(issueDate)}
                            onChange={(e) => {
                                // Set time to noon to avoid timezone issues
                                const dateString = e.target.value;
                                const [year, month, day] = dateString.split('-').map(Number);
                                // Month is 0-indexed in JavaScript Date object
                                const date = new Date(year, month - 1, day, 12, 0, 0);
                                console.log("Selected issue date:", date);
                                setIssueDate(date);
                            }}
                            fullWidth
                            InputLabelProps={{
                                shrink: true,
                            }}
                        />
                    </Grid>
                    
                    <Grid item xs={12} sm={4}>
                        <TextField
                            label="Due Date"
                            type="date"
                            value={formatDateForPicker(dueDate)}
                            onChange={(e) => {
                                // Set time to noon to avoid timezone issues
                                const dateString = e.target.value;
                                const [year, month, day] = dateString.split('-').map(Number);
                                // Month is 0-indexed in JavaScript Date object
                                const date = new Date(year, month - 1, day, 12, 0, 0);
                                console.log("Selected due date:", date);
                                setDueDate(date);
                            }}
                            fullWidth
                            InputLabelProps={{
                                shrink: true,
                            }}
                        />
                    </Grid>
                    
                    <Grid item xs={12} sm={4}>
                        <FormControl fullWidth>
                            <InputLabel id="currency-select-label">Currency</InputLabel>
                            <Select
                                labelId="currency-select-label"
                                value={currency.code}
                                label="Currency"
                                onChange={(e) => {
                                    const selectedCurrency = currencies.find(c => c.code === e.target.value);
                                    if (selectedCurrency) {
                                        setCurrency(selectedCurrency);
                                    }
                                }}
                            >
                                {currencies.map((c) => (
                                    <MenuItem key={c.code} value={c.code}>
                                        {c.symbol} - {c.name}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </Grid>
                    
                    <Grid item xs={12}>
                        <TextField
                            select
                            label="Status"
                            value={status}
                            onChange={(e) => setStatus(e.target.value as any)}
                            fullWidth
                        >
                            <MenuItem value="draft">Draft</MenuItem>
                            <MenuItem value="sent">Sent</MenuItem>
                            <MenuItem value="paid">Paid</MenuItem>
                            <MenuItem value="overdue">Overdue</MenuItem>
                            <MenuItem value="cancelled">Cancelled</MenuItem>
                        </TextField>
                    </Grid>
                </Grid>
                
                <Box sx={{ mt: 4 }}>
                    <Typography variant="h6" gutterBottom>
                        Invoice Items
                    </Typography>
                    
                    <Divider sx={{ mb: 2 }} />
                    
                    {items.map((item, index) => (
                        <Grid container spacing={2} key={item.id} sx={{ mb: 2 }}>
                            <Grid item xs={12} sm={5}>
                                <TextField
                                    label="Description"
                                    value={item.description}
                                    onChange={(e) => handleItemChange(item.id, 'description', e.target.value)}
                                    fullWidth
                                    required
                                />
                            </Grid>
                            
                            <Grid item xs={6} sm={2}>
                                <TextField
                                    label="Quantity"
                                    type="number"
                                    value={item.quantity}
                                    onChange={(e) => handleItemChange(item.id, 'quantity', e.target.value)}
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
                                    onChange={(e) => handleItemChange(item.id, 'unit_price', e.target.value)}
                                    fullWidth
                                    required
                                    InputProps={{
                                        startAdornment: <InputAdornment position="start">{currency.symbol}</InputAdornment>,
                                        inputProps: { min: 0, step: 0.01 }
                                    }}
                                />
                            </Grid>
                            
                            <Grid item xs={10} sm={2}>
                                <TextField
                                    label="Total"
                                    type="number"
                                    value={item.total}
                                    onChange={(e) => handleItemChange(item.id, 'total', e.target.value)}
                                    InputProps={{
                                        startAdornment: <InputAdornment position="start">{currency.symbol}</InputAdornment>,
                                        inputProps: { min: 0, step: 0.01 }
                                    }}
                                    fullWidth
                                />
                            </Grid>
                            
                            <Grid item xs={2} sm={1} sx={{ display: 'flex', alignItems: 'center' }}>
                                <IconButton
                                    color="error"
                                    onClick={() => handleRemoveItem(item.id)}
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
                                    value={subtotal}
                                    onChange={(e) => {
                                        // Allow manual override of the subtotal
                                        const newSubtotal = parseFloat(e.target.value) || 0;
                                        setManualSubtotal(newSubtotal);
                                        
                                        // If items should be updated to match the new subtotal
                                        if (items.length > 0 && calculatedSubtotal > 0) {
                                            const ratio = newSubtotal / calculatedSubtotal;
                                            // Optional: Update items to reflect the new subtotal (distribute proportionally)
                                            /*
                                            setItems(items.map(item => ({
                                                ...item,
                                                total: item.total * ratio
                                            })));
                                            */
                                        }
                                    }}
                                    fullWidth
                                    InputProps={{
                                        startAdornment: <InputAdornment position="start">{currency.symbol}</InputAdornment>,
                                        inputProps: { min: 0, step: 0.01 }
                                    }}
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
                                        value={taxAmount}
                                        onChange={(e) => {
                                            // Calculate tax rate based on entered tax amount
                                            const newTaxAmount = parseFloat(e.target.value) || 0;
                                            if (subtotal > 0) {
                                                setTaxRate((newTaxAmount / subtotal) * 100);
                                            }
                                        }}
                                        fullWidth
                                        InputProps={{
                                            startAdornment: <InputAdornment position="start">{currency.symbol}</InputAdornment>,
                                            inputProps: { min: 0, step: 0.01 }
                                        }}
                                    />
                                </Grid>
                            </Grid>
                            
                            <Divider sx={{ my: 1 }} />
                            
                            <TextField
                                label="Total"
                                type="number"
                                value={total}
                                onChange={(e) => {
                                    // Allow manual override of the total
                                    const newTotal = parseFloat(e.target.value) || 0;
                                    setManualTotal(newTotal);
                                    
                                    // Optionally update tax rate based on the new total
                                    if (subtotal > 0) {
                                        // Calculate the new tax amount based on the difference
                                        const newTaxAmount = newTotal - subtotal;
                                        if (newTaxAmount >= 0) {
                                            // Update the tax rate based on the new tax amount
                                            setTaxRate((newTaxAmount / subtotal) * 100);
                                        }
                                    }
                                }}
                                fullWidth
                                InputProps={{
                                    startAdornment: <InputAdornment position="start">{currency.symbol}</InputAdornment>,
                                    inputProps: { min: 0, step: 0.01 }
                                }}
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
                        onClick={handleSubmit}
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? 'Saving...' : 'Save Changes'}
                    </Button>
                </Box>
            </Paper>
            
            {/* Success Message Snackbar */}
            <Snackbar
                open={showSuccessMessage}
                autoHideDuration={1500}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert severity="success" elevation={6} variant="filled">
                    Invoice updated successfully!
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default InvoiceForm;