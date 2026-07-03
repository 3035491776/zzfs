import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // 通用页面
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', noAuth: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { title: '注册', noAuth: true },
  },

  // 管理员端
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, role: 'admin' },
    redirect: '/admin/dashboard',
    children: [
      { path: 'dashboard', name: 'AdminDashboard', component: () => import('../views/admin/Dashboard.vue'), meta: { title: '数据大屏' } },
      { path: 'books', name: 'BookManage', component: () => import('../views/admin/BookManage.vue'), meta: { title: '图书管理' } },
      { path: 'categories', name: 'CategoryManage', component: () => import('../views/admin/CategoryManage.vue'), meta: { title: '分类管理' } },
      { path: 'borrow-review', name: 'BorrowReview', component: () => import('../views/admin/BorrowReview.vue'), meta: { title: '借阅审核' } },
      { path: 'return-review', name: 'ReturnReview', component: () => import('../views/admin/ReturnReview.vue'), meta: { title: '归还管理' } },
      { path: 'users', name: 'UserManage', component: () => import('../views/admin/UserManage.vue'), meta: { title: '用户管理' } },
      { path: 'seats', name: 'SeatManage', component: () => import('../views/admin/SeatManage.vue'), meta: { title: '座位管理' } },
      { path: 'broadcast', name: 'Broadcast', component: () => import('../views/admin/Broadcast.vue'), meta: { title: '系统通知' } },
      { path: 'profile', name: 'AdminProfile', component: () => import('../views/Profile.vue'), meta: { title: '个人中心' } },
    ],
  },

  // 教师端
  {
    path: '/teacher',
    component: () => import('../views/teacher/TeacherLayout.vue'),
    meta: { requiresAuth: true, role: 'teacher' },
    redirect: '/teacher/books',
    children: [
      { path: 'books', name: 'TeacherBooks', component: () => import('../views/student/BookBrowse.vue'), meta: { title: '图书浏览' } },
      { path: 'my-borrows', name: 'TeacherBorrows', component: () => import('../views/student/MyBorrows.vue'), meta: { title: '我的借阅' } },
      { path: 'seat-reserve', name: 'TeacherSeatReserve', component: () => import('../views/student/SeatReserve.vue'), meta: { title: '自习室预约' } },
      { path: 'ai-assistant', name: 'TeacherAIAssistant', component: () => import('../views/student/AIAssistant.vue'), meta: { title: 'AI助手' } },
      { path: 'library-map', name: 'TeacherLibraryMap', component: () => import('../views/student/LibraryMap.vue'), meta: { title: '图书馆地图' } },
      { path: 'notifications', name: 'TeacherNotifications', component: () => import('../views/student/Notifications.vue'), meta: { title: '消息通知' } },
      { path: 'profile', name: 'TeacherProfile', component: () => import('../views/Profile.vue'), meta: { title: '个人中心' } },
    ],
  },

  // 学生端
  {
    path: '/student',
    component: () => import('../views/student/StudentLayout.vue'),
    meta: { requiresAuth: true, role: 'student' },
    redirect: '/student/books',
    children: [
      { path: 'books', name: 'StudentBooks', component: () => import('../views/student/BookBrowse.vue'), meta: { title: '图书浏览' } },
      { path: 'my-borrows', name: 'StudentBorrows', component: () => import('../views/student/MyBorrows.vue'), meta: { title: '我的借阅' } },
      { path: 'seat-reserve', name: 'SeatReserve', component: () => import('../views/student/SeatReserve.vue'), meta: { title: '自习室预约' } },
      { path: 'ai-assistant', name: 'AIAssistant', component: () => import('../views/student/AIAssistant.vue'), meta: { title: 'AI助手' } },
      { path: 'library-map', name: 'LibraryMap', component: () => import('../views/student/LibraryMap.vue'), meta: { title: '图书馆地图' } },
      { path: 'notifications', name: 'Notifications', component: () => import('../views/student/Notifications.vue'), meta: { title: '消息通知' } },
      { path: 'profile', name: 'StudentProfile', component: () => import('../views/Profile.vue'), meta: { title: '个人中心' } },
    ],
  },

  // 默认跳转
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')

  document.title = to.meta.title ? `${to.meta.title} - 智慧图书馆` : '智慧图书馆管理系统'

  // 未登录 → 只能访问 noAuth 页面
  if (!token || !user) {
    if (to.meta.noAuth) {
      next()
    } else {
      next('/login')
    }
    return
  }

  // 已登录 → 不能访问登录页
  if (to.meta.noAuth) {
    if (user.role === 'admin') next('/admin/dashboard')
    else if (user.role === 'teacher') next('/teacher/books')
    else next('/student/books')
    return
  }

  // 角色校验
  const requiredRole = to.meta.role || to.matched.find(m => m.meta.role)?.meta.role
  if (requiredRole && user.role !== requiredRole) {
    if (user.role === 'admin') next('/admin/dashboard')
    else if (user.role === 'teacher') next('/teacher/books')
    else next('/student/books')
    return
  }

  next()
})

export default router
