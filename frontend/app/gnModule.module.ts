import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterModule, Routes } from '@angular/router';
import { GN2CommonModule } from '@geonature_common/GN2Common.module';
import { NgChartsModule } from 'ng2-charts';
import { IndicatorDetailsComponent } from './components/indicator-details/indicator-details.component';
import { ModuleComponent } from './components/module/module.component';
import { VisualizationBlockComponent } from './components/visualization-block/visualization-block.component';
import { VisualizationChartComponent } from './components/visualization-chart/visualization-chart.component';
import { VisualizationPageComponent } from './components/visualization-page/visualization-page.component';
import { VisualizationParamsFormComponent } from './components/visualization-params-form/visualization-params-form.component';
import { VisualizationScalarComponent } from './components/visualization-scalar/visualization-scalar.component';
import { DataService } from './services/data.service';

const routes: Routes = [
  { path: '', component: ModuleComponent },
  { path: 'indicator/:indicatorId/details', component: IndicatorDetailsComponent },
  { path: 'visualization/:indicatorId/params', component: VisualizationParamsFormComponent },
  { path: 'visualization/:indicatorId', component: VisualizationPageComponent },
];

@NgModule({
  declarations: [
    ModuleComponent,
    IndicatorDetailsComponent,
    VisualizationParamsFormComponent,
    VisualizationPageComponent,
    VisualizationBlockComponent,
    VisualizationChartComponent,
    VisualizationScalarComponent,
  ],
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatTooltipModule,
    ReactiveFormsModule,
    GN2CommonModule,
    NgChartsModule,
  ],
  providers: [DataService],
  bootstrap: [ModuleComponent],
})
export class GeonatureModule {}
