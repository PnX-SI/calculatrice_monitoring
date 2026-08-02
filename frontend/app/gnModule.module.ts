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
import { IndicatorCodeEditorComponent } from './components/indicator-code-editor/indicator-code-editor.component';
import { IndicatorDetailsComponent } from './components/indicator-details/indicator-details.component';
import { IndicatorFormComponent } from './components/indicator-form/indicator-form.component';
import { BarChartVizBlockFormComponent } from './components/indicator-viz-blocks-form/bar-chart-viz-block-form/bar-chart-viz-block-form.component';
import { IndicatorVizBlocksFormComponent } from './components/indicator-viz-blocks-form/indicator-viz-blocks-form.component';
import { ScalarVizBlockFormComponent } from './components/indicator-viz-blocks-form/scalar-viz-block-form/scalar-viz-block-form.component';
import { VizBlockFormComponent } from './components/indicator-viz-blocks-form/viz-block-form/viz-block-form.component';
import { ModuleComponent } from './components/module/module.component';
import { ReferenceTableFormComponent } from './components/reftable-form/reftable-form.component';
import { ReferenceTablesComponent } from './components/reftables/reftables.component';
import { VisualizationBlockComponent } from './components/visualization-block/visualization-block.component';
import { VisualizationChartComponent } from './components/visualization-chart/visualization-chart.component';
import { VisualizationPageComponent } from './components/visualization-page/visualization-page.component';
import { VisualizationParamsFormComponent } from './components/visualization-params-form/visualization-params-form.component';
import { VisualizationScalarComponent } from './components/visualization-scalar/visualization-scalar.component';
import { DataService } from './services/data.service';
import { UtilsService } from './services/utils.service';

const routes: Routes = [
  { path: '', component: ModuleComponent },
  { path: 'indicator/:indicatorId/details', component: IndicatorDetailsComponent },
  { path: 'indicator/create', component: IndicatorFormComponent },
  { path: 'indicator/:indicatorId/edit', component: IndicatorFormComponent },
  { path: 'indicator/:indicatorId/edit-code', component: IndicatorCodeEditorComponent },
  { path: 'indicator/:indicatorId/viz-blocks', component: IndicatorVizBlocksFormComponent },
  { path: 'reference-tables', component: ReferenceTablesComponent },
  { path: 'reference-table/create', component: ReferenceTableFormComponent },
  { path: 'visualization/:indicatorId/params', component: VisualizationParamsFormComponent },
  { path: 'visualization/:indicatorId', component: VisualizationPageComponent },
];

@NgModule({
  declarations: [
    ModuleComponent,
    IndicatorDetailsComponent,
    IndicatorFormComponent,
    IndicatorCodeEditorComponent,
    IndicatorVizBlocksFormComponent,
    VizBlockFormComponent,
    ScalarVizBlockFormComponent,
    BarChartVizBlockFormComponent,
    ReferenceTablesComponent,
    ReferenceTableFormComponent,
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
  providers: [DataService, UtilsService],
  bootstrap: [ModuleComponent],
})
export class GeonatureModule {}
