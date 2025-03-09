import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export interface InvoiceItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface Invoice {
  id: string;
  user_id: string;
  customer_id: string;
  invoice_number: string;
  issue_date: string;
  due_date: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'reminder_sent' | 'cancelled';
  items: InvoiceItem[];
  subtotal: number;
  tax: number;
  tax_rate?: number;  // Tax rate percentage
  total: number;
  notes?: string;
  recipient_email?: string;
  currency_code?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CreateInvoiceData {
  user_id: string;
  customer_id: string;
  invoice_number: string;
  issue_date: string;
  due_date: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'reminder_sent' | 'cancelled';
  items: {
    description: string;
    quantity: number;
    unit_price: number;
    total: number;
  }[];
  subtotal: number;
  tax: number;
  total: number;
  notes?: string;
  recipient_email?: string;
  currency_code?: string;
}

// Configuration for axios requests
const axiosConfig = {
  headers: {
    'Content-Type': 'application/json',
  },
};

export const getInvoices = async (): Promise<Invoice[]> => {
  try {
    const response = await axios.get(`${API_URL}/invoices/`, axiosConfig);
    console.log('Fetched invoices:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching invoices:', error);
    throw error;
  }
};

export const getInvoice = async (id: string): Promise<Invoice> => {
  try {
    const response = await axios.get(`${API_URL}/invoices/${id}`, axiosConfig);
    console.log(`Fetched invoice ${id}:`, response.data);
    return response.data;
  } catch (error) {
    console.error(`Error fetching invoice ${id}:`, error);
    throw error;
  }
};

export const createInvoice = async (data: CreateInvoiceData): Promise<Invoice> => {
  try {
    console.log('Creating invoice with data:', data);
    const response = await axios.post(`${API_URL}/invoices/`, data, axiosConfig);
    console.log('Invoice creation response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error creating invoice:', error);
    if (axios.isAxiosError(error) && error.response) {
      console.error('Error response:', error.response.data);
      throw new Error(error.response.data.detail || 'Failed to create invoice');
    }
    throw error;
  }
};

export const updateInvoice = async (id: string, invoice: Partial<Invoice>): Promise<Invoice> => {
  try {
    console.log(`Updating invoice ${id} with data:`, invoice);

    // Ensure dates are properly formatted
    const preparedData = {
      ...invoice
    };

    const response = await axios.put(`${API_URL}/invoices/${id}`, preparedData, axiosConfig);
    console.log('Invoice update response:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error updating invoice ${id}:`, error);
    if (axios.isAxiosError(error) && error.response) {
      console.error('Error response:', error.response.data);
    }
    throw error;
  }
};

export const deleteInvoice = async (id: string): Promise<void> => {
  try {
    await axios.delete(`${API_URL}/invoices/${id}`, axiosConfig);
    console.log(`Invoice ${id} deleted successfully`);
  } catch (error) {
    console.error(`Error deleting invoice ${id}:`, error);
    throw error;
  }
};

export const getInvoiceStats = async (): Promise<{
  total_invoices: number;
  total_revenue: number;
  status_counts: Record<Invoice['status'], number>;
}> => {
  try {
    const response = await axios.get(`${API_URL}/invoices/stats`, axiosConfig);
    console.log('Fetched invoice stats:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching invoice stats:', error);
    throw error;
  }
};