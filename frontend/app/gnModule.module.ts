import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { RouterModule, Routes } from '@angular/router';
import { GN2CommonModule } from '@geonature_common/GN2Common.module';
import { ModuleComponent } from './components/module/module.component';
import { VisualizationPageComponent } from './components/visualization-page/visualization-page.component';
import { VisualizationParamsFormComponent } from './components/visualization-params-form/visualization-params-form.component';
import { DataService } from './services/data.service';

const routes: Routes = [
  { path: '', component: ModuleComponent },
  { path: 'visualization/:indicatorId/params', component: VisualizationParamsFormComponent },
  { path: 'visualization/:indicatorId', component: VisualizationPageComponent },
];

@NgModule({
  declarations: [ModuleComponent, VisualizationParamsFormComponent, VisualizationPageComponent],
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    MatListModule,
    MatIconModule,
    MatButtonModule,
    ReactiveFormsModule,
    GN2CommonModule,
  ],
  providers: [DataService],
  bootstrap: [ModuleComponent],
})
export class GeonatureModule {}
