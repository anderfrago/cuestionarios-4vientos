import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { tap } from 'rxjs';
import { Aspect, Attempt, Course, User } from './models';

@Injectable({providedIn:'root'})
export class ApiService {
  private http = inject(HttpClient);
  readonly user = signal<User|null>(JSON.parse(localStorage.getItem('user') || 'null'));
  readonly courses = signal<Course[]>([]);
  readonly attempts = signal<Attempt[]>([]);
  readonly loggedIn = computed(() => !!this.user());
  readonly role = computed(() => this.user()?.role ?? null);

  login(email:string,password:string) { return this.http.post<{access_token:string;user:User}>('/api/auth/login',{email,password}).pipe(tap(r=>{localStorage.setItem('token',r.access_token);localStorage.setItem('user',JSON.stringify(r.user));this.user.set(r.user)})); }
  register(data:{name:string;email:string;password:string}) { return this.http.post('/api/auth/register',data); }
  logout() { localStorage.clear(); this.user.set(null); this.courses.set([]); }
  loadMe() { return this.http.get<{user:User;courses:Course[]}>('/api/me').pipe(tap(r=>{this.user.set(r.user);this.courses.set(r.courses)})); }
  join(code:string) { return this.http.post<Course>('/api/courses/join',{code}).pipe(tap(c=>this.courses.update(v=>[...v.filter(x=>x.id!==c.id),c]))); }
  questionnaire(courseId:number) { return this.http.get<{course:Course;scale:{value:number;label:string}[];aspects:Aspect[]}>(`/api/courses/${courseId}/questionnaire`); }
  submit(courseId:number, answers:{item_id:number;value:number}[]) { return this.http.post<Attempt>(`/api/courses/${courseId}/attempts`,{answers}); }
  loadAttempts() { return this.http.get<Attempt[]>('/api/attempts').pipe(tap(v=>this.attempts.set(v))); }
  analytics(courseId:number) { return this.http.get<{course:Course;summary:{aspect:string;average:number;count:number}[];attempts:Attempt[]}>(`/api/courses/${courseId}/analytics`); }
  adminCourses() { return this.http.get<Course[]>('/api/admin/courses'); }
  createCourse(data:Partial<Course>) { return this.http.post<Course>('/api/admin/courses',data); }
  updateCourse(id:number,data:Partial<Course>) { return this.http.put<Course>(`/api/admin/courses/${id}`,data); }
  users() { return this.http.get<User[]>('/api/admin/users'); }
  createUser(data:Partial<User>&{password?:string}) { return this.http.post<User>('/api/admin/users',data); }
  updateUser(id:number,data:Partial<User>) { return this.http.put<User>(`/api/admin/users/${id}`,data); }
  aspects() { return this.http.get<Aspect[]>('/api/admin/aspects'); }
  updateAspect(id:number,data:Partial<Aspect>&Record<string,unknown>) { return this.http.put<Aspect>(`/api/admin/aspects/${id}`,data); }
  createItem(data:Partial<import('./models').Item>) { return this.http.post('/api/admin/items',data); }
  updateItem(id:number,data:Partial<import('./models').Item>) { return this.http.put(`/api/admin/items/${id}`,data); }
}

