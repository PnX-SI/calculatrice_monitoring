import { Injectable } from '@angular/core';
import { ModuleService } from '@geonature/services/module.service';

@Injectable()
export class PermissionService {
  constructor(private _moduleService: ModuleService) {}

  public getPermission(perm: string): number {
    return this._moduleService.currentModule.cruved[perm] || 0;
  }

  public getAdminPermission(perm: string): number {
    return this._moduleService.currentModule.module_objects.CALC_ADMIN_INDICATOR?.cruved[perm] || 0;
  }
}
