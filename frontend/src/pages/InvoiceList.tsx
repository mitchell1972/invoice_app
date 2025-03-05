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
import { deleteInvoice, getInvoices } from '../api/invoices';
import { formatCurrency, formatDate } from '../utils/format';

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

  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: getInvoices,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteInvoice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      setDeleteId(null);
    },
  });

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, id: string) => {
    setAnchorEl(event.currentTarget);
    setSelectedInvoice(id);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedInvoice(null);
  };

  const columns: GridColDef[] = [
    { field: 'invoice_number', headerName: 'Invoice #', flex: 1 },
    { 
      field: 'customer',
      headerName: 'Customer',
      flex: 1,
      valueGetter: (params) => params.row.customer?.name || '',
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
      valueFormatter: (params) => formatCurrency(params.value),
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

  return (
    <Box sx={{ height: 600, width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4" component="h1">
          Invoices
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => navigate('/invoices/new')}
        >
          New Invoice
        </Button>
      </Box>

      <DataGrid
        rows={invoices}
        columns={columns}
        loading={isLoading}
        pageSizeOptions={[5, 10, 25]}
        initialState={{
          pagination: { paginationModel: { pageSize: 10 } },
        }}
      />

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
          setDeleteId(selectedInvoice);
          handleMenuClose();
        }}>
          Delete
        </MenuItem>
      </Menu>

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
    </Box>
  );
} 