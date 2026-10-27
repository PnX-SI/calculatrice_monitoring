import { Injectable } from '@angular/core';
import { CanDeactivate } from '@angular/router';
import { Observable } from 'rxjs';

export interface CanComponentDeactivate {
  canDeactivate: () => boolean | Observable<boolean>;
}

@Injectable({
  providedIn: 'root',
})
export class CanDeactivateGuard implements CanDeactivate<CanComponentDeactivate> {
  canDeactivate(targetComponent: CanComponentDeactivate): boolean | Observable<boolean> {
    return targetComponent.canDeactivate ? targetComponent.canDeactivate() : true;
  }
}
