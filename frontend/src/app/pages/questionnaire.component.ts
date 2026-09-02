import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../core/api.service';
import { Attempt, Course, FormQuestion, FormResponseInput, FormVersion, Questionnaire } from '../core/models';

@Component({
  standalone: true,
  imports: [FormsModule],
  templateUrl: './questionnaire.component.html'
})
export class QuestionnaireComponent implements OnInit {

  private route = inject(ActivatedRoute);
  api = inject(ApiService);
  router = inject(Router);
  course = signal<Course | null>(null);
  forms = signal<Questionnaire[]>([]); selected = signal<Questionnaire | null>(null);
  version = signal<FormVersion | null>(null);
  values = signal<Record<string, { option_id?: number | null; text_value?: string }>>({});
  result = signal<Attempt | null>(null);
  message = signal('');

  requiredKeys = computed(() => { const keys: string[] = []; for (const a of this.version()?.aspects || []) for (const q of a.questions) if (q.required) { if (q.rows.length) for (const r of q.rows) keys.push(this.key(q, r.id!)); else keys.push(this.key(q, null)) } return keys });

  progress = computed(() => { const keys = this.requiredKeys(); if (!keys.length) return 100; const done = keys.filter(k => { const v = this.values()[k]; return !!(v?.option_id || v?.text_value?.trim()) }).length; return done / keys.length * 100 });
  ngOnInit() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.api.courseForms(id).subscribe(r => {
      this.course.set(r.course);
      this.forms.set(r.forms)
    })
  }
  open(form: Questionnaire) {
    this.api.formDefinition(this.course()!.id, form.version_id!).subscribe(r => {
      this.selected.set(r.questionnaire);
      this.version.set(r.version); this.values.set({});
      this.message.set('')
    }
    )
  }

  key(q: FormQuestion, rowId: number | null | undefined) {
    return `${q.id}:${rowId ?? ''}`
  }
  option(q: FormQuestion, rowId: number | null = null) {
    return this.values()[this.key(q, rowId)]?.option_id ?? null
  }
  text(q: FormQuestion, rowId: number | null = null) {
    return this.values()[this.key(q, rowId)]?.text_value ?? ''
  }
  setOption(q: FormQuestion, rowId: number | null, optionId: number | null) {
    this.values.update(v => ({
      ...v, [this.key(q, rowId)]: { ...v[this.key(q, rowId)], option_id: optionId }
    }))
  }
  setText(q: FormQuestion, rowId: number | null, value: string) {
    this.values.update(v => ({
      ...v, [this.key(q, rowId)]: { ...v[this.key(q, rowId)], text_value: value }
    }))
  }
  submit() {
    const responses: FormResponseInput[] = Object.entries(this.values()).map(([key, value]) => {
      const [question, row] = key.split(':');
      return { question_id: +question, row_id: row ? +row : null, ...value }
    });
    this.api.submitForm(this.course()!.id, this.version()!.id, responses).subscribe({ next: r => this.result.set(r), error: e => this.message.set(e.error?.error || 'No se pudieron guardar las respuestas') })
  }
}
