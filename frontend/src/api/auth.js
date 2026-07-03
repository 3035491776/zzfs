import request from './request'

export const authApi = {
  login: (data) => request.post('/auth/login', data),
  loginSms: (data) => request.post('/auth/login/sms', data),
  register: (data) => request.post('/auth/register', data),
  logout: () => request.post('/auth/logout'),
  getMe: () => request.get('/auth/me'),
  sendSms: (phone) => request.post('/auth/sms/send', { phone }),
  getCaptcha: () => request.get('/captcha/image'),
}

export const userApi = {
  list: (params) => request.get('/users', { params }),
  getProfile: () => request.get('/users/profile'),
  updateProfile: (data) => request.put('/users/profile', data),
  changePassword: (data) => request.put('/users/password', data),
  toggleStatus: (id) => request.put(`/users/${id}/status`),
  resetPassword: (id) => request.post(`/users/${id}/reset-password`),
}

export const bookApi = {
  list: (params) => request.get('/books', { params }),
  get: (id) => request.get(`/books/${id}`),
  add: (data) => request.post('/books', data),
  update: (id, data) => request.put(`/books/${id}`, data),
  delete: (id) => request.delete(`/books/${id}`),
}

export const categoryApi = {
  list: (params) => request.get('/categories', { params }),
  add: (data) => request.post('/categories', data),
  update: (id, data) => request.put(`/categories/${id}`, data),
  delete: (id) => request.delete(`/categories/${id}`),
}

export const borrowApi = {
  list: (params) => request.get('/borrows', { params }),
  myBorrows: (params) => request.get('/borrows/my', { params }),
  apply: (bookId) => request.post('/borrows', { book_id: bookId }),
  approve: (id) => request.put(`/borrows/${id}/approve`),
  reject: (id) => request.put(`/borrows/${id}/reject`),
  return: (id) => request.put(`/borrows/${id}/return`),
  renew: (id) => request.put(`/borrows/${id}/renew`),
}

export const seatApi = {
  list: (params) => request.get('/seats', { params }),
  get: (id) => request.get(`/seats/${id}`),
  add: (data) => request.post('/seats', data),
  update: (id, data) => request.put(`/seats/${id}`, data),
  delete: (id) => request.delete(`/seats/${id}`),
  getSlots: (seatId, date) => request.get(`/reservations/seats/${seatId}/slots`, { params: { date } }),
  reserve: (seatId, data) => request.post(`/reservations/seats/${seatId}/reserve`, data),
  checkin: (resId) => request.post(`/reservations/reservations/${resId}/checkin`),
  cancel: (resId) => request.post(`/reservations/reservations/${resId}/cancel`),
  myReservations: (params) => request.get('/reservations/reservations/my', { params }),
  allReservations: (params) => request.get('/reservations/reservations', { params }),
}

export const dashboardApi = {
  stats: () => request.get('/dashboard/stats'),
  borrowTrend: () => request.get('/dashboard/borrow-trend'),
  categoryChart: () => request.get('/dashboard/category-chart'),
  popularBooks: () => request.get('/dashboard/popular-books'),
  seatUsage: () => request.get('/dashboard/seat-usage'),
  userActivity: () => request.get('/dashboard/user-activity'),
}

export const aiApi = {
  chat: (message) => request.post('/ai/chat', { message }),
  recommend: () => request.get('/ai/recommend'),
  conversations: () => request.get('/ai/conversations'),
}

export const notificationApi = {
  list: (params) => request.get('/notifications', { params }),
  unreadCount: () => request.get('/notifications/unread-count'),
  markRead: (id) => request.put(`/notifications/${id}/read`),
  markAllRead: () => request.put('/notifications/read-all'),
}

export const mapApi = {
  libraryInfo: () => request.get('/map/library-info'),
  nearby: (keyword) => request.get('/map/nearby', { params: { keyword } }),
}

export const excelApi = {
  importBooks: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/excel/import/books', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  exportBooks: () => request.get('/excel/export/books', { responseType: 'blob' }),
  exportBorrows: () => request.get('/excel/export/borrows', { responseType: 'blob' }),
  downloadTemplate: () => request.get('/excel/template/books', { responseType: 'blob' }),
}

export const bookRequestApi = {
  submit: (data) => request.post('/book-requests', data),
  my: (params) => request.get('/book-requests/my', { params }),
  all: (params) => request.get('/book-requests', { params }),
  approve: (id, data) => request.put(`/book-requests/${id}/approve`, data),
  reject: (id, data) => request.put(`/book-requests/${id}/reject`, data),
}

export const seatRepairApi = {
  submit: (data) => request.post('/seat-repairs', data),
  my: (params) => request.get('/seat-repairs/my', { params }),
  all: (params) => request.get('/seat-repairs', { params }),
  fix: (id) => request.put(`/seat-repairs/${id}/fix`),
  resolve: (id, data) => request.put(`/seat-repairs/${id}/resolve`, data),
  reject: (id, data) => request.put(`/seat-repairs/${id}/reject`, data),
}

export const broadcastApi = {
  send: (data) => request.post('/broadcast', data),
}

export const adminApi = {
  pendingCounts: () => request.get('/admin/counts'),
}
