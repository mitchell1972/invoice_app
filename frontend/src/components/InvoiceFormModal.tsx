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
    Paper
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
    onSave: (invoiceData: CreateInvoiceData) => Promise<void>;
    customer: Customer | null;
}

const InvoiceFormModal: React.FC<InvoiceFormModalProps> = ({
                                                               open,
                                                               onClose,
                                                               onSave,
                                                               customer
                                                           }) => {
    const [invoiceNumber, setInvoiceNumber] = useState(`INV-${Date.now()}`);
    const [issueDate, setIssueDate] = useState<Date>(new Date());
    const [dueDate, setDueDate] = useState<Date>(new Date(Date.now() + 30 * 24 * 60 * 60 * 1000));
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

    // Format date as YYYY-MM-DD string
    const formatDateToISOString = (date: Date): string => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
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

    // Format customer address from address fields
    const formatCustomerAddress = (): string => {
        if (!customer) return '';

        const addressParts = [];

        if (customer.address) addressParts.push(customer.address);
        if (customer.city) addressParts.push(customer.city);
        if (customer.state) addressParts.push(customer.state);
        if (customer.postal_code) addressParts.push(customer.postal_code);
        if (customer.country) addressParts.push(customer.country);

        return addressParts.join(', ');
    };

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

        setIsSubmitting(true);

        try {
            const invoiceData: CreateInvoiceData = {
                invoice_number: invoiceNumber,
                customer_id: customer.id,
                issue_date: formatDateToISOString(issueDate),
                due_date: formatDateToISOString(dueDate),
                status,
                subtotal,
                tax: taxAmount,
                total,
                notes,
                recipient_email: recipientEmail,
                currency_code: currency.code,
                items: items.map(({ id, ...item }) => item) // Remove the temporary id
            };

            await onSave(invoiceData);
            onClose();
        } catch (error) {
            console.error('Error saving invoice:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    // If there's no customer, don't render the modal
    if (!customer) return null;

    return (
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
                                <strong>Issue Date:</strong> {formatDateToISOString(issueDate)}
                            </Typography>
                            <Typography variant="body2">
                                <strong>Due Date:</strong> {formatDateToISOString(dueDate)}
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
                                value={formatDateToISOString(issueDate)}
                                onChange={(e) => setIssueDate(new Date(e.target.value))}
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
                                value={formatDateToISOString(dueDate)}
                                onChange={(e) => setDueDate(new Date(e.target.value))}
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
                    {isSubmitting ? 'Saving...' : 'Save Invoice'}
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default InvoiceFormModal;