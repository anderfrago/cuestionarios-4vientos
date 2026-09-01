import { Routes } from '@angular/router';
import { authGuard, roleGuard } from './core/guards';
export const routes:Routes=[
 {path:'',pathMatch:'full',redirectTo:'panel'},
 {path:'acceso',loadComponent:()=>import('./pages/login.component').then(m=>m.LoginComponent)},
 {path:'panel',canActivate:[authGuard],loadComponent:()=>import('./pages/dashboard.component').then(m=>m.DashboardComponent)},
 {path:'cuestionario/:id',canActivate:[authGuard,roleGuard(['student'])],loadComponent:()=>import('./pages/questionnaire.component').then(m=>m.QuestionnaireComponent)},
 {path:'resultados/:id',canActivate:[authGuard,roleGuard(['tutor','admin'])],loadComponent:()=>import('./pages/analytics.component').then(m=>m.AnalyticsComponent)},
 {path:'administracion',canActivate:[authGuard,roleGuard(['admin'])],loadComponent:()=>import('./pages/admin.component').then(m=>m.AdminComponent)},
 {path:'**',redirectTo:'panel'}];

