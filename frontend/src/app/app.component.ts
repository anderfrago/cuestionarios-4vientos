import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterOutlet } from '@angular/router';
import { ApiService } from './core/api.service';
@Component({selector:'app-root',imports:[RouterOutlet,RouterLink],template:`
<nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm"><div class="container"><a class="navbar-brand fw-semibold" routerLink="/panel">Autopercepción</a>
@if(api.loggedIn()){<div class="d-flex align-items-center gap-3 text-white"><span class="small d-none d-md-inline">{{api.user()?.name}}</span>@if(api.role()==='admin'){<a class="btn btn-outline-light btn-sm" routerLink="/administracion">Administración</a>}<button class="btn btn-light btn-sm" (click)="logout()">Salir</button></div>}</div></nav>
<main><router-outlet/></main><footer class="border-top py-4 mt-5"><div class="container small text-secondary">Cuatrovientos · <a href="https://cuatrovientos.org/rgpd/" target="_blank" rel="noopener">Privacidad y RGPD</a></div></footer>`})
export class AppComponent { api=inject(ApiService); router=inject(Router); logout(){this.api.logout();this.router.navigate(['/acceso']);} }

