import { useState } from 'react';
import {
    Box,
    Button,
    Typography,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Chip,
    IconButton,
    Menu,
    MenuItem,
    Paper,
    CircularProgress
} from '@mui/material';
import {
    DataGrid,
    GridColDef,
    GridRenderCellParams,
} from '@mui/x-data-grid';
import {
    MoreVert as MoreVertIcon,
    Add as AddIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteInvoice, getInvoices, updateInvoice } from '../api/invoices';
import { formatDate } from '../utils/format';

// Define the InvoiceStatus type to match your backend
type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';

// Define a type for currency codes
type CurrencyCode = 'USD' | 'GBP' | 'EUR';

// Currency symbol mapping with type safety
const currencySymbols: Record<CurrencyCode, string> = {
    USD: '$',
    GBP: '£',
    EUR: '€'
};

const getStatusColor = (status: string): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
    const colors: Record<string, "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning"> = {
        draft: 'default',
        sent: 'primary',
        paid: 'success',
        overdue: 'error',
        cancelled: 'error',
    };
    return colors[status] || 'default';
};

export default function InvoiceList() {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [deleteId, setDeleteId] = useState<string | null>(null);
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [selectedInvoice, setSelectedInvoice] = useState<string | null>(null);

    // State for status change
    const [statusChangeOpen, setStatusChangeOpen] = useState(false);
    const [statusInvoiceId, setStatusInvoiceId] = useState<string | null>(null);

    const { data: invoices = [], isLoading } = useQuery({
        queryKey: ['invoices'],
        queryFn: getInvoices,
        refetchInterval: 3000, // Refresh every 3 seconds to ensure invoices are up-to-date
    });

    const deleteMutation = useMutation({
        mutationFn: deleteInvoice,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['invoices'] });
            setDeleteId(null);
        },
    });

    const updateStatusMutation = useMutation({
        mutationFn: ({id, status}: {id: string, status: InvoiceStatus}) =>
            updateInvoice(id, { status }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['invoices'] });
            setStatusChangeOpen(false);
            setStatusInvoiceId(null);
        }
    });

    const handleMenuClick = (event: React.MouseEvent<HTMLElement>, id: string) => {
        setAnchorEl(event.currentTarget);
        setSelectedInvoice(id);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
        setSelectedInvoice(null);
    };

    const handleUpdateStatus = (status: InvoiceStatus) => {
        if (!statusInvoiceId) return;
        updateStatusMutation.mutate({id: statusInvoiceId, status});
    };

    const handleStatusChangeClick = (id: string) => {
        setStatusInvoiceId(id);
        setStatusChangeOpen(true);
        handleMenuClose();
    };

    const columns: GridColDef[] = [
        { field: 'invoice_number', headerName: 'Invoice #', flex: 1 },
        {
            field: 'customer_id',
            headerName: 'Customer',
            flex: 1,
            valueGetter: (params) => {
                const customer = params.row.customer || {};
                return customer.name || 'Unknown';
            }
        },
        {
            field: 'issue_date',
            headerName: 'Issue Date',
            flex: 1,
            valueFormatter: (params) => formatDate(params.value),
        },
        {
            field: 'due_date',
            headerName: 'Due Date',
            flex: 1,
            valueFormatter: (params) => formatDate(params.value),
        },
        {
            field: 'total',
            headerName: 'Total',
            flex: 1,
            renderCell: (params: GridRenderCellParams) => {
                const currencyCode = (params.row.currency_code || 'USD') as CurrencyCode;
                const symbol = currencySymbols[currencyCode] || '$';
                return `${symbol} ${Number(params.value).toFixed(2)}`;
            }
        },
        {
            field: 'status',
            headerName: 'Status',
            flex: 1,
            renderCell: (params: GridRenderCellParams) => (
                <Chip
                    label={params.value.toUpperCase()}
                    color={getStatusColor(params.value)}
                    size="small"
                />
            ),
        },
        {
            field: 'actions',
            headerName: 'Actions',
            flex: 1,
            renderCell: (params) => (
                <Box>
                    <IconButton
                        size="small"
                        onClick={(e) => handleMenuClick(e, params.row.id)}
                    >
                        <MoreVertIcon />
                    </IconButton>
                </Box>
            ),
        },
    ];

    if (isLoading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h4" component="h1">
                    Invoices
                </Typography>
                <Button
                    variant="contained"
                    color="primary"
                    startIcon={<AddIcon />}
                    onClick={() => navigate('/customers')}
                >
                    New Invoice
                </Button>
            </Box>

            <Paper sx={{ height: 600, width: '100%' }}>
                <DataGrid
                    rows={invoices}
                    columns={columns}
                    loading={isLoading}
                    pageSizeOptions={[5, 10, 25]}
                    initialState={{
                        pagination: { paginationModel: { pageSize: 10 } },
                    }}
                />
            </Paper>

            <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
            >
                <MenuItem onClick={() => {
                    navigate(`/invoices/${selectedInvoice}`);
                    handleMenuClose();
                }}>
                    View/Edit
                </MenuItem>
                <MenuItem onClick={() => {
                    if (selectedInvoice) {
                        handleStatusChangeClick(selectedInvoice);
                    }
                }}>
                    Change Status
                </MenuItem>
                <MenuItem onClick={() => {
                    setDeleteId(selectedInvoice);
                    handleMenuClose();
                }}>
                    Delete
                </MenuItem>
            </Menu>

            {/* Delete Confirmation Dialog */}
            <Dialog open={!!deleteId} onClose={() => setDeleteId(null)}>
                <DialogTitle>Confirm Delete</DialogTitle>
                <DialogContent>
                    Are you sure you want to delete this invoice?
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteId(null)}>Cancel</Button>
                    <Button
                        color="error"
                        onClick={() => deleteId && deleteMutation.mutate(deleteId)}
                    >
                        Delete
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Status Change Dialog */}
            <Dialog open={statusChangeOpen} onClose={() => setStatusChangeOpen(false)}>
                <DialogTitle>Change Invoice Status</DialogTitle>
                <DialogContent>
                    <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <Button
                            variant="outlined"
                            onClick={() => handleUpdateStatus('draft')}
                            sx={{ justifyContent: 'flex-start', mb: 1 }}
                        >
                            <Chip label="DRAFT" color="default" size="small" sx={{ mr: 2 }} />
                            Mark as Draft
                        </Button>

                        <Button
                            variant="outlined"
                            color="primary"
                            onClick={() => handleUpdateStatus('sent')}
                            sx={{ justifyContent: 'flex-start', mb: 1 }}
                        >
                            <Chip label="SENT" color="primary" size="small" sx={{ mr: 2 }} />
                            Mark as Sent
                        </Button>

                        <Button
                            variant="outlined"
                            color="success"
                            onClick={() => handleUpdateStatus('paid')}
                            sx={{ justifyContent: 'flex-start', mb: 1 }}
                        >
                            <Chip label="PAID" color="success" size="small" sx={{ mr: 2 }} />
                            Mark as Paid
                        </Button>

                        <Button
                            variant="outlined"
                            color="error"
                            onClick={() => handleUpdateStatus('cancelled')}
                            sx={{ justifyContent: 'flex-start' }}
                        >
                            <Chip label="CANCELLED" color="error" size="small" sx={{ mr: 2 }} />
                            Mark as Cancelled
                        </Button>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setStatusChangeOpen(false)}>Cancel</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}