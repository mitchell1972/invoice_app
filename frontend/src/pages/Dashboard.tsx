import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  CircularProgress,
} from '@mui/material';
import {
  People as PeopleIcon,
  Receipt as ReceiptIcon,
  AttachMoney as MoneyIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { getCustomers } from '../api/customers';
import { getInvoices } from '../api/invoices';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  loading?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, loading }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Grid container spacing={3} alignItems="center">
        <Grid item>
          {icon}
        </Grid>
        <Grid item>
          <Typography color="textSecondary" gutterBottom variant="overline">
            {title}
          </Typography>
          <Typography variant="h4">
            {loading ? <CircularProgress size={20} /> : value}
          </Typography>
        </Grid>
      </Grid>
    </CardContent>
  </Card>
);

export default function Dashboard() {
  const { 
    data: customers = [], 
    isLoading: customersLoading 
  } = useQuery({
    queryKey: ['customers'],
    queryFn: getCustomers,
  });

  const { 
    data: invoices = [], 
    isLoading: invoicesLoading 
  } = useQuery({
    queryKey: ['invoices'],
    queryFn: getInvoices,
  });

  // Calculate statistics
  const totalCustomers = customers.length;
  const totalInvoices = invoices.length;
  const totalRevenue = invoices.reduce((sum, invoice) => sum + Number(invoice.total), 0);
  const draftInvoices = invoices.filter(invoice => invoice.status === 'draft').length;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Customers"
            value={totalCustomers}
            icon={<PeopleIcon sx={{ fontSize: 40, color: 'primary.main' }} />}
            loading={customersLoading}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Invoices"
            value={totalInvoices}
            icon={<ReceiptIcon sx={{ fontSize: 40, color: 'info.main' }} />}
            loading={invoicesLoading}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Revenue"
            value={`$${totalRevenue.toLocaleString()}`}
            icon={<MoneyIcon sx={{ fontSize: 40, color: 'success.main' }} />}
            loading={invoicesLoading}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Draft Invoices"
            value={draftInvoices}
            icon={<AssignmentIcon sx={{ fontSize: 40, color: 'warning.main' }} />}
            loading={invoicesLoading}
          />
        </Grid>
      </Grid>
    </Box>
  );
} 