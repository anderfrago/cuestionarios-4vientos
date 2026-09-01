import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../core/api.service';
import { Attempt, Course, FormQuestion, FormResponseInput, FormVersion, Questionnaire } from '../core/models';

@Component({standalone:true,imports:[FormsModule],template:`
<div class="container py-5" style="max-width:1000px">
@if(result()){<div class="card shadow-sm p-5 text-center"><p class="text-primary fw-semibold">Formulario completado</p><h1 class="h2">{{result()?.encouragement}}</h1><div class="row g-3 my-4">@for(r of result()?.results;track r.aspect_id){<div class="col-md-4"><div class="bg-light rounded-4 p-3 h-100"><div class="display-score">{{r.average}}</div><strong>{{r.aspect}}</strong><div class="small text-primary">{{r.level}}</div><p class="small mt-2 mb-0">{{r.message}}</p></div></div>}</div><button class="btn btn-primary" (click)="router.navigate(['/panel'])">Volver al panel</button></div>}
@else if(!version()){<p class="text-primary fw-semibold mb-1">{{course()?.name}}</p><h1 class="h2">Formularios disponibles</h1><div class="row g-3 mt-3">@for(form of forms();track form.id){<div class="col-md-6"><div class="card shadow-sm p-4 h-100"><span class="badge text-bg-light align-self-start">Versión {{form.version}}</span><h2 class="h4 mt-3">{{form.name}}</h2><p class="text-secondary">{{form.description}}</p><p class="small">Intentos realizados en esta versión: {{form.attempt_count}}</p><button class="btn btn-primary mt-auto" (click)="open(form)">Completar</button></div></div>}@empty{<div class="alert alert-info">No hay formularios publicados asignados a este curso.</div>}</div>}
@else{<button class="btn btn-link px-0 mb-2" (click)="version.set(null)">← Volver a formularios</button><p class="text-primary fw-semibold mb-1">{{course()?.name}}</p><h1 class="h2">{{selected()?.name}}</h1><p class="text-secondary">{{selected()?.description}}</p><div class="progress mb-4"><div class="progress-bar" [style.width.%]="progress()"></div></div>
@for(aspect of version()?.aspects;track aspect.id){<section class="mb-5"><h2 class="h4">{{aspect.name}}</h2><p class="text-secondary">{{aspect.description}}</p>@for(q of aspect.questions;track q.id){<div class="card question-card shadow-sm p-4 mb-3"><div class="d-flex gap-2"><p class="fw-semibold mb-1">{{q.title}}</p>@if(q.required){<span class="text-danger" title="Obligatoria">*</span>}@if(q.is_critical){<span class="badge text-bg-danger align-self-start">Respuesta protegida</span>}</div>@if(q.help_text){<p class="small text-secondary">{{q.help_text}}</p>}
@if(q.question_type==='text'){<textarea class="form-control" rows="3" [ngModel]="text(q)" (ngModelChange)="setText(q,null,$event)"></textarea>}
@else if(q.question_type==='select'){<select class="form-select" [ngModel]="option(q)" (ngModelChange)="setOption(q,null,$event)"><option [ngValue]="null">Selecciona una opción</option>@for(o of q.options;track o.id){<option [ngValue]="o.id">{{o.label}}</option>}</select>}
@else if(q.question_type==='matrix'||q.question_type==='number_matrix'){<div class="table-responsive"><table class="table table-sm align-middle"><thead><tr><th>Elemento</th>@for(o of q.options;track o.id){<th class="text-center">{{o.label}}</th>}</tr></thead><tbody>@for(row of q.rows;track row.id){<tr><th class="fw-normal">{{row.label}}</th>@for(o of q.options;track o.id){<td class="text-center"><input class="form-check-input" type="radio" [name]="key(q,row.id)" [checked]="option(q,row.id)===o.id" (change)="setOption(q,row.id!,o.id!)"></td>}</tr>@if(q.allow_other && row.label.toLowerCase().startsWith('otra')){<tr><td colspan="99"><input class="form-control form-control-sm" placeholder="Especifica tu respuesta" [ngModel]="text(q,row.id)" (ngModelChange)="setText(q,row.id!,$event)"></td></tr>}}</tbody></table></div>}
@else{<div class="d-flex flex-column gap-2">@for(o of q.options;track o.id){<label class="form-check"><input class="form-check-input" type="radio" [name]="key(q,null)" [checked]="option(q)===o.id" (change)="setOption(q,null,o.id!)"><span class="form-check-label">{{o.label}}</span></label>}</div>}
@if(q.allow_other && !(q.question_type==='matrix'||q.question_type==='number_matrix')){<input class="form-control mt-3" placeholder="Otra respuesta" [ngModel]="text(q)" (ngModelChange)="setText(q,null,$event)">}
</div>}</section>}@if(message()){<div class="alert alert-danger">{{message()}}</div>}<button class="btn btn-primary btn-lg" [disabled]="progress()<100" (click)="submit()">Enviar respuestas</button>}
</div>`})
export class QuestionnaireComponent implements OnInit {
  private route=inject(ActivatedRoute); api=inject(ApiService); router=inject(Router);
  course=signal<Course|null>(null); forms=signal<Questionnaire[]>([]); selected=signal<Questionnaire|null>(null);
  version=signal<FormVersion|null>(null); values=signal<Record<string,{option_id?:number|null;text_value?:string}>>({});
  result=signal<Attempt|null>(null); message=signal('');
  requiredKeys=computed(()=>{const keys:string[]=[];for(const a of this.version()?.aspects||[])for(const q of a.questions)if(q.required){if(q.rows.length)for(const r of q.rows)keys.push(this.key(q,r.id!));else keys.push(this.key(q,null))}return keys});
  progress=computed(()=>{const keys=this.requiredKeys();if(!keys.length)return 100;const done=keys.filter(k=>{const v=this.values()[k];return !!(v?.option_id||v?.text_value?.trim())}).length;return done/keys.length*100});
  ngOnInit(){const id=Number(this.route.snapshot.paramMap.get('id'));this.api.courseForms(id).subscribe(r=>{this.course.set(r.course);this.forms.set(r.forms)})}
  open(form:Questionnaire){this.api.formDefinition(this.course()!.id,form.version_id!).subscribe(r=>{this.selected.set(r.questionnaire);this.version.set(r.version);this.values.set({});this.message.set('')})}
  key(q:FormQuestion,rowId:number|null|undefined){return `${q.id}:${rowId??''}`}
  option(q:FormQuestion,rowId:number|null=null){return this.values()[this.key(q,rowId)]?.option_id??null}
  text(q:FormQuestion,rowId:number|null=null){return this.values()[this.key(q,rowId)]?.text_value??''}
  setOption(q:FormQuestion,rowId:number|null,optionId:number|null){this.values.update(v=>({...v,[this.key(q,rowId)]:{...v[this.key(q,rowId)],option_id:optionId}}))}
  setText(q:FormQuestion,rowId:number|null,value:string){this.values.update(v=>({...v,[this.key(q,rowId)]:{...v[this.key(q,rowId)],text_value:value}}))}
  submit(){const responses:FormResponseInput[]=Object.entries(this.values()).map(([key,value])=>{const [question,row]=key.split(':');return {question_id:+question,row_id:row?+row:null,...value}});this.api.submitForm(this.course()!.id,this.version()!.id,responses).subscribe({next:r=>this.result.set(r),error:e=>this.message.set(e.error?.error||'No se pudieron guardar las respuestas')})}
}
