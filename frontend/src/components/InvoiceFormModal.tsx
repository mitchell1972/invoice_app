import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    Grid,
    Typography,
    Box,
    IconButton,
    Divider,
    MenuItem,
    InputAdornment,
    FormControl,
    InputLabel,
    Select,
    Paper,
    Snackbar,
    Alert
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { Customer } from '../api/customers';
import { CreateInvoiceData } from '../api/invoices';

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

interface InvoiceFormModalProps {
    open: boolean;
    onClose: () => void;
    onSave: (data: CreateInvoiceData) => Promise<void>;
    customer: Customer | null;
    onNavigateToInvoices?: () => void; // Add navigation callback
}

const InvoiceFormModal: React.FC<InvoiceFormModalProps> = ({
                                                               open,
                                                               onClose,
                                                               onSave,
                                                               customer,
                                                               onNavigateToInvoices
                                                           }) => {
    const [invoiceNumber, setInvoiceNumber] = useState(`INV-${Date.now()}`);
    // Initialize state with default values
    const [issueDate, setIssueDate] = useState<Date>(new Date());
    const [dueDate, setDueDate] = useState<Date>(new Date());
    
    // Initialize dates when the component mounts
    useEffect(() => {
        // Initialize dates with noon time to avoid timezone issues
        const today = new Date();
        const initialIssueDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 12, 0, 0);
        
        // Set due date to 30 days in the future
        const initialDueDate = new Date(initialIssueDate);
        initialDueDate.setDate(initialDueDate.getDate() + 30);
        
        setIssueDate(initialIssueDate);
        setDueDate(initialDueDate);
    }, []);
    const [status, setStatus] = useState<'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled'>('draft');
    const [notes, setNotes] = useState('');
    const [recipientEmail, setRecipientEmail] = useState('');
    const [currency, setCurrency] = useState<Currency>({ code: 'USD', symbol: '$', name: 'US Dollar' });
    const [items, setItems] = useState<InvoiceItem[]>([
        {
            id: '1',
            description: '',
            quantity: 1,
            unit_price: 0,
            total: 0
        }
    ]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showSuccessMessage, setShowSuccessMessage] = useState(false);

    // Available currencies
    const currencies: Currency[] = [
        { code: 'USD', symbol: '$', name: 'US Dollar' },
        { code: 'GBP', symbol: '£', name: 'British Pound' },
        { code: 'EUR', symbol: '€', name: 'Euro' }
    ];

    // Calculate totals
    const subtotal = items.reduce((sum, item) => sum + item.total, 0);
    const taxRate = 20; // 20% VAT
    const taxAmount = subtotal * (taxRate / 100);
    const total = subtotal + taxAmount;

    // Format date for display in the date picker (YYYY-MM-DD format)
    const formatDateForPicker = (date: Date): string => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    // Format date as ISO string for API (which FastAPI expects for datetime objects)
    const formatDateToISOString = (date: Date): string => {
        return date.toISOString();
    };

    // Format currency display
    const formatCurrency = (amount: number): string => {
        return `${currency.symbol} ${amount.toFixed(2)}`;
    };

    // Initialize recipient email from customer if available
    useEffect(() => {
        if (customer) {
            setRecipientEmail(customer.email || '');
        }
    }, [customer]);

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
        if (!customer) return;

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
            
            // Create the invoice data
            const invoiceData: CreateInvoiceData = {
                invoice_number: invoiceNumber,
                user_id: customer.user_id || '00000000-0000-0000-0000-000000000000', // Add user_id
                customer_id: customer.id,
                issue_date: formatDateToISOString(issueDateTime),
                due_date: formatDateToISOString(dueDateTime),
                status,
                subtotal,
                tax: taxAmount,
                total,
                notes,
                recipient_email: recipientEmail,
                currency_code: currency.code,
                items: validItems
            };

            await onSave(invoiceData);
            
            // Show success message immediately
            setShowSuccessMessage(true);
            
            // Close the modal after a brief delay to show the success message
            setTimeout(() => {
                // First close the modal
                onClose();
                
                // Then redirect to invoices page
                if (onNavigateToInvoices) {
                    console.log("Navigating to invoices list");
                    onNavigateToInvoices();
                }
            }, 1500);
        } catch (error) {
            console.error('Error saving invoice:', error);
            // Show error message
            alert('Failed to save invoice. Please check all required fields and try again.');
            // Also display more details in the console
            if (error instanceof Error) {
                console.error('Error details:', error.message);
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    // If there's no customer, don't render the modal
    if (!customer) return null;

    return (
        <>
            <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
                <DialogTitle>
                    <Typography variant="h5">Create New Invoice</Typography>
                    <Typography variant="subtitle1" color="textSecondary">
                        For: {customer.name}
                    </Typography>
                </DialogTitle>

                <DialogContent>
                    {/* Customer Information Section */}
                    <Paper variant="outlined" sx={{ p: 2, mb: 3, bgcolor: 'background.paper' }}>
                        <Grid container spacing={2}>
                            <Grid item xs={12} md={6}>
                                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                                    Bill To:
                                </Typography>
                                <Typography variant="body1" gutterBottom><strong>{customer.name}</strong></Typography>
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
                            <Grid item xs={12} md={6}>
                                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                                    Invoice Details:
                                </Typography>
                                <Typography variant="body2">
                                    <strong>Invoice Number:</strong> {invoiceNumber}
                                </Typography>
                                <Typography variant="body2">
                                    <strong>Issue Date:</strong> {formatDateForPicker(issueDate)}
                                </Typography>
                                <Typography variant="body2">
                                    <strong>Due Date:</strong> {formatDateForPicker(dueDate)}
                                </Typography>
                            </Grid>
                        </Grid>
                    </Paper>

                    <Box sx={{ mt: 2 }}>
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
                                </TextField>
                            </Grid>
                        </Grid>
                    </Box>

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
                                        value={item.total.toFixed(2)}
                                        InputProps={{
                                            startAdornment: <InputAdornment position="start">{currency.symbol}</InputAdornment>,
                                            readOnly: true
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
                                <Typography variant="subtitle1">Subtotal: {formatCurrency(subtotal)}</Typography>
                                <Typography variant="subtitle1">Tax ({taxRate}%): {formatCurrency(taxAmount)}</Typography>
                                <Divider sx={{ my: 1 }} />
                                <Typography variant="h6">Total: {formatCurrency(total)}</Typography>
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
                </DialogContent>

                <DialogActions>
                    <Button onClick={onClose}>Cancel</Button>
                    <Button
                        onClick={handleSubmit}
                        variant="contained"
                        color="primary"
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? 'Saving...' : 'Save and Close'}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Success Message Snackbar */}
            <Snackbar
                open={showSuccessMessage}
                autoHideDuration={1500}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert severity="success" elevation={6} variant="filled">
                    Invoice saved successfully!
                </Alert>
            </Snackbar>
        </>
    );
};

export default InvoiceFormModal;