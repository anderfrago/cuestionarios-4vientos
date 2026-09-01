import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from './api.service';
export const authGuard=()=>inject(ApiService).loggedIn() || inject(Router).createUrlTree(['/acceso']);
export const roleGuard=(roles:string[])=>()=>roles.includes(inject(ApiService).role()||'') || inject(Router).createUrlTree(['/panel']);

