import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ModuleComponent } from './components/module/module.component';

const routes: Routes = [{ path: '', component: ModuleComponent }];

@NgModule({
  declarations: [ModuleComponent],
  imports: [CommonModule, RouterModule.forChild(routes)],
  bootstrap: [ModuleComponent],
})
export class GeonatureModule {}
