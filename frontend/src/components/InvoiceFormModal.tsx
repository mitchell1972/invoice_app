import React, { useState } from 'react';
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
    InputAdornment
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { format } from 'date-fns';
import { Customer } from '../api/customers';
import { CreateInvoiceData } from '../api/invoices';
import { generateInvoiceNumber } from '../utils/format';

interface InvoiceItem {
    id: string;
    description: string;
    quantity: number;
    unit_price: number;
    total: number;
}

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
    const [invoiceNumber, setInvoiceNumber] = useState(generateInvoiceNumber());
    const [issueDate, setIssueDate] = useState<Date>(new Date());
    const [dueDate, setDueDate] = useState<Date>(new Date(Date.now() + 30 * 24 * 60 * 60 * 1000));
    const [status, setStatus] = useState<'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled'>('draft');
    const [notes, setNotes] = useState('');
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

    // Calculate totals
    const subtotal = items.reduce((sum, item) => sum + item.total, 0);
    const taxRate = 20; // 20% VAT
    const taxAmount = subtotal * (taxRate / 100);
    const total = subtotal + taxAmount;

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
                issue_date: format(issueDate, 'yyyy-MM-dd'),
                due_date: format(dueDate, 'yyyy-MM-dd'),
                status,
                subtotal,
                tax: taxAmount,
                total,
                notes,
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
                <LocalizationProvider dateAdapter={AdapterDateFns}>
                    <Box sx={{ mt: 2 }}>
                        <Grid container spacing={3}>
                            <Grid item xs={12} sm={4}>
                                <TextField
                                    label="Invoice Number"
                                    value={invoiceNumber}
                                    onChange={(e) => setInvoiceNumber(e.target.value)}
                                    fullWidth
                                    required
                                />
                            </Grid>

                            <Grid item xs={12} sm={4}>
                                <DatePicker
                                    label="Issue Date"
                                    value={issueDate}
                                    onChange={(date) => date && setIssueDate(date)}
                                    format="yyyy-MM-dd"
                                />
                            </Grid>

                            <Grid item xs={12} sm={4}>
                                <DatePicker
                                    label="Due Date"
                                    value={dueDate}
                                    onChange={(date) => date && setDueDate(date)}
                                    format="yyyy-MM-dd"
                                />
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
                                            startAdornment: <InputAdornment position="start">$</InputAdornment>,
                                            inputProps: { min: 0, step: 0.01 }
                                        }}
                                    />
                                </Grid>

                                <Grid item xs={10} sm={2}>
                                    <TextField
                                        label="Total"
                                        value={item.total.toFixed(2)}
                                        InputProps={{
                                            startAdornment: <InputAdornment position="start">$</InputAdornment>,
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
                                <Typography variant="subtitle1">Subtotal: ${subtotal.toFixed(2)}</Typography>
                                <Typography variant="subtitle1">Tax ({taxRate}%): ${taxAmount.toFixed(2)}</Typography>
                                <Divider sx={{ my: 1 }} />
                                <Typography variant="h6">Total: ${total.toFixed(2)}</Typography>
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
                </LocalizationProvider>
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