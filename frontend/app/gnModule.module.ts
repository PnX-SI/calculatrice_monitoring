import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ModuleComponent } from './components/module/module.component';

import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { DataService } from './services/data.service';

const routes: Routes = [{ path: '', component: ModuleComponent }];

@NgModule({
  declarations: [ModuleComponent],
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    MatListModule,
    MatIconModule,
    MatButtonModule,
  ],
  providers: [DataService],
  bootstrap: [ModuleComponent],
})
export class GeonatureModule {}
