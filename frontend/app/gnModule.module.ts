import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { RouterModule, Routes } from '@angular/router';
import { GN2CommonModule } from '@geonature_common/GN2Common.module';
import { NgChartsModule } from 'ng2-charts';
import { ModuleComponent } from './components/module/module.component';
import { VisualizationBlockComponent } from './components/visualization-block/visualization-block.component';
import { VisualizationChartComponent } from './components/visualization-chart/visualization-chart.component';
import { VisualizationPageComponent } from './components/visualization-page/visualization-page.component';
import { VisualizationParamsFormComponent } from './components/visualization-params-form/visualization-params-form.component';
import { VisualizationScalarComponent } from './components/visualization-scalar/visualization-scalar.component';
import { DataService } from './services/data.service';

const routes: Routes = [
  { path: '', component: ModuleComponent },
  { path: 'visualization/:indicatorId/params', component: VisualizationParamsFormComponent },
  { path: 'visualization/:indicatorId', component: VisualizationPageComponent },
];

@NgModule({
  declarations: [
    ModuleComponent,
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
    ReactiveFormsModule,
    GN2CommonModule,
    NgChartsModule,
  ],
  providers: [DataService],
  bootstrap: [ModuleComponent],
})
export class GeonatureModule {}
