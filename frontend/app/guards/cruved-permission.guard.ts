import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, Router } from '@angular/router';
import { ModuleService } from '@geonature/services/module.service';
import { ToastrService } from 'ngx-toastr';

/**
 * Guards a route behind a CRUVED permission.
 * Configure via route data, e.g.:
 *   { path: '...', canActivate: [CruvedPermissionGuard], data: { permission: 'U', permissionObject: 'CALC_ADMIN_INDICATOR' } }
 * To test the CRUVED permission directly on the module leave the `permissionObject` undefined (passing 'ALL' won't work).
 */
@Injectable()
export class CruvedPermissionGuard implements CanActivate {
  constructor(
    private _moduleService: ModuleService,
    private _router: Router,
    private _toastr: ToastrService
  ) {}

  canActivate(route: ActivatedRouteSnapshot): boolean {
    const permission: string = route.data.permission;
    const permissionObject: string | undefined = route.data.permissionObject;
    const fallbackRoute = ''; // GeoNature home page
    let hasPermission;
    if (permissionObject)
      hasPermission =
        (this._moduleService.currentModule.module_objects[permissionObject]?.cruved[permission] ||
          0) > 0;
    else hasPermission = (this._moduleService.currentModule.cruved[permission] || 0) > 0;
    if (!hasPermission) {
      this._toastr.error(
        "Vous n'avez pas les permissions nécessaires pour accéder à cette page.",
        'Erreur',
        { disableTimeOut: true, tapToDismiss: false, closeButton: true, easeTime: 0 }
      );
      this._router.navigate([fallbackRoute]);
    }
    return hasPermission;
  }
}
