import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export interface InvoiceItem {
  id?: string;
  invoice_id?: string;
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface Invoice {
  id?: string;
  invoice_number: string;
  customer_id: string;
  issue_date: string;
  due_date: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  subtotal: number;
  tax: number;
  total: number;
  notes?: string;
  recipient_email?: string;  // New field for recipient email
  currency_code?: string;    // New field for currency
  created_at?: string;
  updated_at?: string;
  items: InvoiceItem[];
}

export interface CreateInvoiceData extends Omit<Invoice, 'id' | 'created_at' | 'updated_at'> {}

export const getInvoices = async (): Promise<Invoice[]> => {
  const response = await axios.get(`${API_URL}/invoices`);
  return response.data;
};

export const getInvoice = async (id: string): Promise<Invoice> => {
  const response = await axios.get(`${API_URL}/invoices/${id}`);
  return response.data;
};

export const createInvoice = async (invoice: CreateInvoiceData): Promise<Invoice> => {
  console.log('Creating invoice with data:', invoice);
  const response = await axios.post(`${API_URL}/invoices`, invoice);
  return response.data;
};

export const updateInvoice = async (id: string, invoice: Partial<Invoice>): Promise<Invoice> => {
  const response = await axios.put(`${API_URL}/invoices/${id}`, invoice);
  return response.data;
};

export const deleteInvoice = async (id: string): Promise<void> => {
  await axios.delete(`${API_URL}/invoices/${id}`);
};

export const getInvoiceStats = async (): Promise<{
  total_invoices: number;
  total_revenue: number;
  status_counts: Record<Invoice['status'], number>;
}> => {
  const response = await axios.get(`${API_URL}/invoices/stats`);
  return response.data;
};