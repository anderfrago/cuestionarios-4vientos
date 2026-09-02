import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../core/api.service';
import { Attempt, Course, CriticalAlert } from '../core/models';

@Component({
    standalone: true, 
    imports: [DatePipe, FormsModule],
     templateUrl: './analytics.component.html',
    })
export class AnalyticsComponent implements OnInit {

    private api = inject(ApiService);
    private route = inject(ActivatedRoute);
    course = signal<Course | null>(null);
    summary = signal<{ aspect: string; average: number; count: number }[]>([]);
    attempts = signal<(Attempt & { questionnaire?: { name: string }; version?: number; source?: string })[]>([]); alerts = signal<CriticalAlert[]>([]);
    notes: Record<number, string> = {};
    unreviewed = () => this.alerts().filter(a => !a.reviewed_at).length;

    ngOnInit() {
        this.load()
    }

    load() {
        this.api.formAnalytics(Number(this.route.snapshot.paramMap.get('id'))).subscribe(r => {
            this.course.set(r.course);
            this.summary.set(r.summary);
            this.attempts.set(r.attempts as never);
            this.alerts.set(r.alerts)
        })
    }

    review(a: CriticalAlert) {
        this.api.reviewAlert(a.id, this.notes[a.id] || '').subscribe(() =>
            this.load())
    } downloadXlsx() {
        this.api.download(`/api/courses/${this.course()!.id}/export.xlsx`,
            `${this.course()!.name}-respuestas.xlsx`)
    } downloadPdf() { this.api.download(`/api/courses/${this.course()!.id}/export.pdf`, `${this.course()!.name}-informe.pdf`) } individualPdf(id: number) { this.api.download(`/api/attempts/${id}/export.pdf`, `intento-${id}.pdf`) }
}
