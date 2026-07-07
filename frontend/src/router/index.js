import { createRouter, createWebHistory } from 'vue-router'

const userPageRoutes = [
  { key: 'books', path: 'books', component: () => import('../views/student/BookBrowse.vue'), title: '图书浏览' },
  { key: 'myBorrows', path: 'my-borrows', component: () => import('../views/student/MyBorrows.vue'), title: '我的借阅' },
  { key: 'seatReserve', path: 'seat-reserve', component: () => import('../views/student/SeatReserve.vue'), title: '自习室预约' },
  { key: 'aiAssistant', path: 'ai-assistant', component: () => import('../views/student/AIAssistant.vue'), title: 'AI助手' },
  { key: 'libraryMap', path: 'library-map', component: () => import('../views/student/LibraryMap.vue'), title: '图书馆地图' },
  { key: 'notifications', path: 'notifications', component: () => import('../views/student/Notifications.vue'), title: '消息通知' },
  { key: 'profile', path: 'profile', component: () => import('../views/Profile.vue'), title: '个人中心' },
]

const userRouteNames = {
  student: {
    books: 'StudentBooks',
    myBorrows: 'StudentBorrows',
    seatReserve: 'SeatReserve',
    aiAssistant: 'AIAssistant',
    libraryMap: 'LibraryMap',
    notifications: 'Notifications',
    profile: 'StudentProfile',
  },
  teacher: {
    books: 'TeacherBooks',
    myBorrows: 'TeacherBorrows',
    seatReserve: 'TeacherSeatReserve',
    aiAssistant: 'TeacherAIAssistant',
    libraryMap: 'TeacherLibraryMap',
    notifications: 'TeacherNotifications',
    profile: 'TeacherProfile',
  },
}

function createUserChildren(role) {
  return userPageRoutes.map(route => ({
    path: route.path,
    name: userRouteNames[role][route.key],
    component: route.component,
    meta: { title: route.title },
  }))
}

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
    component: () => import('../views/user/UserLayout.vue'),
    meta: { requiresAuth: true, role: 'teacher' },
    redirect: '/teacher/books',
    children: createUserChildren('teacher'),
  },

  // 学生端
  {
    path: '/student',
    component: () => import('../views/user/UserLayout.vue'),
    meta: { requiresAuth: true, role: 'student' },
    redirect: '/student/books',
    children: createUserChildren('student'),
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
