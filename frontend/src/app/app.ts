
import { CommonModule } from '@angular/common';
import {
  Component,
  OnInit,
  ChangeDetectorRef,
  inject
} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { forkJoin } from 'rxjs';

interface DashboardStats {
  total_readings: number;
  total_sensors: number;
  avg_soil_moisture: number | null;
  avg_temperature: number | null;
  avg_air_humidity: number | null;
  total_alerts: number;
  critical_alerts: number;
}

interface Reading {
  id: string;
  sensor_id: string;
  crop_id: string;
  soil_moisture: number;
  temperature: number;
  air_humidity: number;
  recorded_at: string;
  created_at: string;
  alert_count: number;
}

interface AgriculturalAlert {
  id: number;
  reading_id: string;
  alert_type: string;
  severity: string;
  message: string;
  created_at: string;
  sensor_id: string;
  crop_id: string;
  soil_moisture: number;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {

  private http = inject(HttpClient);
  private cdr = inject(ChangeDetectorRef);

  private readonly apiUrl = 'http://127.0.0.1:8000/api';

  // Permite utilizar Math.min() desde la plantilla HTML
  readonly Math = Math;

  stats: DashboardStats = {
    total_readings: 0,
    total_sensors: 0,
    avg_soil_moisture: null,
    avg_temperature: null,
    avg_air_humidity: null,
    total_alerts: 0,
    critical_alerts: 0
  };

  readings: Reading[] = [];
  alerts: AgriculturalAlert[] = [];

  loading = true;
  errorMessage = '';
  lastUpdated = new Date();

  activeSection = 'dashboard';
  mobileMenuOpen = false;

  ngOnInit(): void {
    this.loadDashboard();
  }

  loadDashboard(): void {
    this.loading = true;
    this.errorMessage = '';

    forkJoin({
      stats: this.http.get<DashboardStats>(
        `${this.apiUrl}/dashboard`
      ),
      readings: this.http.get<Reading[]>(
        `${this.apiUrl}/readings?limit=8`
      ),
      alerts: this.http.get<AgriculturalAlert[]>(
        `${this.apiUrl}/alerts?limit=6`
      )
    }).subscribe({


      
next: (data) => {
  console.log('DATOS RECIBIDOS:', data);

  this.stats = data.stats;
  this.readings = data.readings;
  this.alerts = data.alerts;
  this.lastUpdated = new Date();
  this.loading = false;

  this.cdr.markForCheck();

  console.log('ESTADÍSTICAS ASIGNADAS:', this.stats);
  console.log('LECTURAS ASIGNADAS:', this.readings.length);
  console.log('ALERTAS ASIGNADAS:', this.alerts.length);
},

      error: (error) => {
        console.error(
          'Error loading AgroConnect data:',
          error
        );

        this.errorMessage =
          'No fue posible cargar los datos. Verifica que FastAPI y PostgreSQL estén funcionando.';

        this.loading = false;
      }
    });
  }

  navigate(section: string): void {
    this.activeSection = section;
    this.mobileMenuOpen = false;

    const element = document.getElementById(section);

    element?.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  }

  getMoistureClass(value: number): string {
    if (value < 30) {
      return 'status-low';
    }

    if (value > 70) {
      return 'status-high';
    }

    return 'status-normal';
  }

  getSeverityClass(severity: string): string {
    const value = severity.toLowerCase();

    if (
      value === 'high' ||
      value === 'critical' ||
      value === 'alta'
    ) {
      return 'severity-high';
    }

    if (
      value === 'medium' ||
      value === 'moderate' ||
      value === 'media'
    ) {
      return 'severity-medium';
    }

    return 'severity-low';
  }

  getSeverityLabel(severity: string): string {
    const labels: Record<string, string> = {
      high: 'Alta',
      critical: 'Crítica',
      medium: 'Media',
      moderate: 'Moderada',
      low: 'Baja',
      alta: 'Alta',
      media: 'Media',
      baja: 'Baja'
    };

    return labels[severity.toLowerCase()] ?? severity;
  }

  getAlertLabel(type: string): string {
    const labels: Record<string, string> = {
      low_soil_moisture: 'Humedad baja',
      high_temperature: 'Temperatura alta',
      abnormal_air_humidity: 'Humedad del aire',
      low_air_humidity: 'Humedad del aire baja',
      high_air_humidity: 'Humedad del aire alta'
    };

    return labels[type] ?? type.replaceAll('_', ' ');
  }

  formatDate(value: string): string {
    if (!value) {
      return 'Sin fecha';
    }

    return new Intl.DateTimeFormat('es-CO', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    }).format(new Date(value));
  }

  formatNumber(
    value: number | null | undefined
  ): string {
    if (value === null || value === undefined) {
      return '--';
    }

    return new Intl.NumberFormat('es-CO', {
      maximumFractionDigits: 1
    }).format(value);
  }

  get maxReadingsTemperature(): number {
    return Math.max(
      1,
      ...this.readings.map(
        (reading) => reading.temperature
      )
    );
  }

  get chartReadings(): Reading[] {
    return [...this.readings]
      .slice(0, 7)
      .reverse();
  }

  trackByReading(
    _index: number,
    reading: Reading
  ): string {
    return reading.id;
  }

  trackByAlert(
    _index: number,
    alert: AgriculturalAlert
  ): number {
    return alert.id;
  }
}
